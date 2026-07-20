"""DeepSeek bulk audit — sadece is_audited=false sorulari denetler.

POST /api/v2/admin/audit/deepseek/bulk
  - Supabase'den is_audited=false sorulari ceker
  - Her soru icin DeepSeek API'dan Python cozumu uretir
  - Test case'leri subprocess (python3) ile calistirir
  - Tum testleri gecenleri DB'de is_audited=true + audit_status=passed isaretler
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dependencies import get_current_user
from routers.audit import _run_single_test
from supabase_client import get_supabase_admin

router = APIRouter(
    prefix="/api/v2/admin/audit/deepseek",
    tags=["deepseek-bulk-audit"],
    dependencies=[Depends(get_current_user)],
)
log = logging.getLogger("pymulakat.deepseek-audit")

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")


class BulkAuditResponse(BaseModel):
    total: int
    passed: int
    failed: int
    skipped: int
    errors: List[Dict[str, Any]] = []
    results: List[Dict[str, Any]] = []


def _build_prompt(description: str, function_name: str, test_cases: Any, starter_code: str | None = None) -> str:
    tests = json.dumps(test_cases, ensure_ascii=False, indent=2)
    starter = f"\nBAŞLANGIÇ KODU:\n{starter_code}" if starter_code else ""
    return f"""Sen deneyimli bir Python yazılımcısısın. Aşağıdaki soruyu çöz.

SORU: {description}

FONKSİYON ADI: {function_name}

TEST CASES (girdi/çıktı):
{tests}{starter}

KURALLAR:
1. Sadece {function_name} fonksiyonunu yaz
2. Type hint kullan
3. Pythonic, temiz kod
4. Kısayol fonksiyonları YASAK (sorted, set, Counter, defaultdict, bisect, heapq)
5. Sadece saf Python (built-in) kullan
6. Test case'lerdeki tüm senaryoları karşıla

Sadece Python kodunu döndür (açıklama yok, sadece kod):
```python
def {function_name}(...):
    ...
```"""


def _call_deepseek(prompt: str) -> str:
    """DeepSeek chat completion — OpenAI-uyumlu response format."""
    if not DEEPSEEK_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="DEEPSEEK_API_KEY env tanımlı değil.",
        )

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Sen deneyimli bir Python yazılımcısısın. "
                    "Sadece saf Python ile yaz, kısayol YASAK. "
                    "Sadece kod döndür, açıklama yok."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 1500,
    }

    try:
        r = requests.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        log.error("DeepSeek API request failed: %s", e)
        raise HTTPException(status_code=502, detail=f"DeepSeek API request failed: {e}")

    try:
        data = r.json()
    except ValueError as e:
        log.error("DeepSeek response JSON parse error: %s", e)
        raise HTTPException(status_code=502, detail=f"DeepSeek JSON parse error: {e}")

    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail=f"Unexpected DeepSeek response type: {type(data).__name__}")

    if "error" in data:
        err_msg = data["error"].get("message", str(data["error"]))[:300]
        log.error("DeepSeek API error: %s", err_msg)
        raise HTTPException(status_code=502, detail=f"DeepSeek API error: {err_msg}")

    choices = data.get("choices", [])
    if not choices:
        log.error("DeepSeek empty choices: %s", json.dumps(data)[:300])
        raise HTTPException(status_code=502, detail="DeepSeek empty choices")

    content = choices[0].get("message", {}).get("content", "")
    if not content:
        log.error("DeepSeek empty content: %s", json.dumps(choices[0])[:300])
        raise HTTPException(status_code=502, detail="DeepSeek empty content")

    # ```python ... ``` temizle
    code = content.strip()
    if code.startswith("```"):
        lines = code.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        code = "\n".join(lines).strip()

    return code


def _mark(question_id: int, passed: bool) -> None:
    """DB'de is_audited, audit_status, audited_at güncelle."""
    sb = get_supabase_admin()
    update = {
        "is_audited": passed,
        "audit_status": "passed" if passed else "failed",
        "audited_at": "now()",
    }
    sb.table("questions").update(update).eq("id", question_id).execute()


@router.post("/bulk", response_model=BulkAuditResponse)
async def bulk_audit_deepseek(max_questions: int = 50):
    """Sadece is_audited=false sorulari DeepSeek ile denetle."""
    if not DEEPSEEK_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="DEEPSEEK_API_KEY env tanımlı değil.",
        )

    sb = get_supabase_admin()
    try:
        result = (
            sb.table("questions")
            .select("id, title, description, function_name, starter_code, test_cases")
            .eq("is_audited", False)
            .limit(max_questions)
            .execute()
        )
        questions = result.data or []
    except Exception as e:
        log.exception("Bulk audit list failed")
        raise HTTPException(status_code=500, detail=f"List error: {e}")

    passed_count = 0
    failed_count = 0
    skipped_count = 0
    errors = []
    results = []

    for q in questions:
        qid = q.get("id")
        title = q.get("title", "")
        description = q.get("description", "")
        fn_name = q.get("function_name", "")
        test_cases = q.get("test_cases", [])
        starter_code = q.get("starter_code")

        if not description or not fn_name or not test_cases:
            skipped_count += 1
            errors.append({"id": qid, "title": title, "error": "Eksik alan (description/function_name/test_cases)"})
            continue

        # 1) DeepSeek ile kod uret
        prompt = _build_prompt(description, fn_name, test_cases, starter_code)
        try:
            code = _call_deepseek(prompt)
        except HTTPException as e:
            failed_count += 1
            err_msg = str(e.detail)[:300]
            errors.append({"id": qid, "title": title, "stage": "generate", "error": err_msg})
            results.append({"id": qid, "title": title, "status": "failed", "stage": "generate", "error": err_msg})
            continue
        except Exception as e:
            failed_count += 1
            err_msg = str(e)[:300]
            errors.append({"id": qid, "title": title, "stage": "generate", "error": err_msg})
            results.append({"id": qid, "title": title, "status": "failed", "stage": "generate", "error": err_msg})
            continue

        # 2) Test case'leri calistir
        test_results = []
        all_passed = True
        try:
            for tc in test_cases:
                tr = _run_single_test(code, fn_name, tc)
                test_results.append(tr.model_dump() if hasattr(tr, "model_dump") else tr.dict())
                if not tr.passed:
                    all_passed = False
        except Exception as e:
            failed_count += 1
            err_msg = str(e)[:300]
            errors.append({"id": qid, "title": title, "stage": "run", "error": err_msg})
            results.append({"id": qid, "title": title, "status": "failed", "stage": "run", "error": err_msg})
            continue

        # 3) DB'de isaretle
        try:
            _mark(qid, all_passed)
        except Exception as e:
            err_msg = str(e)[:300]
            errors.append({"id": qid, "title": title, "stage": "mark", "error": err_msg})

        if all_passed:
            passed_count += 1
        else:
            failed_count += 1

        results.append({
            "id": qid,
            "title": title,
            "status": "passed" if all_passed else "failed",
            "tests": f"{sum(1 for r in test_results if r.get('passed'))}/{len(test_results)}",
        })

    return BulkAuditResponse(
        total=len(questions),
        passed=passed_count,
        failed=failed_count,
        skipped=skipped_count,
        errors=errors[:20],
        results=results,
    )
