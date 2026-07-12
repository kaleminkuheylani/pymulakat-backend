"""Admin denetim endpointleri (urllib-only, httpx Railway DNS bozuk).

Endpointler:
  GET  /admin/audit/list            → tüm sorular (audit status ile)
  GET  /admin/audit/stats           → dashboard özeti
  GET  /admin/audit/status/{id}     → tek soru audit durumu
  POST /admin/audit/generate        → API (OpenAI/Gemini/Mavis) ile kod üret
  POST /admin/audit/run             → subprocess + timeout ile test
  POST /admin/audit/mark            → DB'de is_audited güncelle
  GET  /admin/audit/debug/network   → outbound DNS testi
"""

import os
import json
import logging
import subprocess
import tempfile
import time
import urllib.request
import urllib.error
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from supabase_client import get_supabase_admin

router = APIRouter(prefix="/audit", tags=["admin-audit"])  # /api/v2/admin (admin.py) + /audit
log = logging.getLogger("pymulakat.audit")

# API config — Gemini OpenAI uyumlu
# Key sırası: GOOGLE_API_KEY / GEMINI_API_KEY (Gemini) → OPENAI → MAVIS_API_KEY
# MAVIS_API_KEY env'de Mavis key olabilir (sk-cp-...) — Gemini reddeder
MAVIS_API_KEY = (
    os.environ.get("GOOGLE_API_KEY")
    or os.environ.get("GEMINI_API_KEY")
    or os.environ.get("OPENAI_API_KEY")
    or os.environ.get("MAVIS_API_KEY")
    or ""
)
# Base URL: MAVIS_API_BASE → OPENAI_API_BASE → default OpenAI
# Hardcoded Gemini OpenAI-uyumlu (Railway env override YOK)
MAVIS_API_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"
# Hardcoded Gemini model (env override YOK)
MAVIS_MODEL = "gemini-1.5-flash"
EXEC_TIMEOUT = 8


# ═══════════════════════════════════════════════════════════════
# ─── Pydantic Models ─────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

class GenerateRequest(BaseModel):
    question_id: int
    description: str
    function_name: str
    test_cases: List[Dict[str, Any]]
    starter_code: Optional[str] = None


class GenerateResponse(BaseModel):
    code: str
    model: str
    tokens_used: int
    elapsed_ms: int


class RunRequest(BaseModel):
    question_id: int
    code: str
    test_cases: List[Dict[str, Any]]
    function_name: str


class TestResult(BaseModel):
    input: Any
    expected: Any
    actual: Any
    passed: bool
    error: Optional[str] = None


class RunResponse(BaseModel):
    passed_count: int
    failed_count: int
    total: int
    results: List[TestResult]
    stderr: Optional[str] = None
    elapsed_ms: int


class MarkRequest(BaseModel):
    question_id: int
    passed: bool


class QuestionSummary(BaseModel):
    id: int
    title: str
    category: str
    level: str
    slug: Optional[str] = None
    is_audited: bool
    audit_status: str
    audited_at: Optional[str] = None
    description: Optional[str] = None
    function_name: Optional[str] = None
    starter_code: Optional[str] = None
    test_cases: Optional[List[Dict[str, Any]]] = None


# ═══════════════════════════════════════════════════════════════
# ─── 1) Soru listesi (audit status) ────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("/list", response_model=List[QuestionSummary])
def list_questions():
    """Tüm soruları audit durumu ile döndür.

    Kolonlar (is_audited, audit_status, audited_at) henüz eklenmediyse
    fallback: temel sorgu + default audit alanları.
    """
    sb = get_supabase_admin()
    try:
        result = (
            sb.table("questions")
            .select(
                "id, title, category, level, slug, is_audited, audit_status, audited_at, "
                "description, function_name, starter_code, test_cases"
            )
            .order("id", desc=False)
            .execute()
        )
        return result.data or []
    except Exception as e1:
        err_str = str(e1)
        if "PGRST116" in err_str or "is_audited" in err_str or "404" in err_str or "Could not find" in err_str:
            log.warning("Audit kolonları yok, fallback temel sorgu")
            try:
                result = (
                    sb.table("questions")
                    .select("id, title, category, level, slug, description, function_name, starter_code, test_cases")
                    .order("id", desc=False)
                    .execute()
                )
                rows = result.data or []
                for r in rows:
                    r.setdefault("is_audited", False)
                    r.setdefault("audit_status", "pending")
                    r.setdefault("audited_at", None)
                return rows
            except Exception as e2:
                log.exception("Fallback list failed")
                raise HTTPException(status_code=500, detail=f"List error (fallback): {e2}")
        log.exception("List questions failed")
        raise HTTPException(status_code=500, detail=f"List error: {e1}")


# ═══════════════════════════════════════════════════════════════
# ─── 2) API ile kod üret (urllib, sync) ────────────────────
# ═══════════════════════════════════════════════════════════════

def _build_prompt(req: GenerateRequest) -> str:
    tests = json.dumps(req.test_cases, ensure_ascii=False, indent=2)
    return f"""Sen deneyimli bir Python yazılımcısısın. Aşağıdaki soruyu çöz.

SORU: {req.description}

FONKSİYON ADI: {req.function_name}

TEST CASES (giriş/çıkış):
{tests}

KURALLAR:
1. Sadece {req.function_name} fonksiyonunu yaz
2. Type hint kullan
3. Pythonic, temiz kod
4. Kısayol fonksiyonları YASAK (sorted, set, Counter, defaultdict, bisect, heapq)
5. Sadece saf Python (built-in) kullan
6. Test case'lerdeki tüm senaryoları karşıla

Sadece Python kodunu döndür (açıklama yok, sadece kod):
```python
def {req.function_name}(...):
    ...
```"""


@router.post("/generate", response_model=GenerateResponse)
async def generate_code(req: GenerateRequest):
    """API (OpenAI/Gemini/Mavis) ile doğru kodu üret. urllib (httpx Railway DNS bozuk)."""
    if not MAVIS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="API key env tanımlı değil (MAVIS_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY / GEMINI_API_KEY).",
        )

    prompt = _build_prompt(req)
    start = time.time()

    # URL: tam path değilse /chat/completions ekle
    url = MAVIS_API_BASE
    if not url.endswith("/chat/completions") and not url.endswith("/chatcompletion_v2"):
        url = f"{MAVIS_API_BASE}/chat/completions"

    body = json.dumps({
        "model": MAVIS_MODEL,
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
    }).encode("utf-8")

    # subprocess curl: Railway DNS bozuk, curl çalışıyor
    try:
        result = subprocess.run(
            ["curl", "-sS", "-X", "POST", url,
             "-H", f"Authorization: Bearer {MAVIS_API_KEY}",
             "-H", "Content-Type: application/json",
             "--data-binary", body.decode("utf-8"),
             "--max-time", "30"],
            capture_output=True, text=True, timeout=35,
        )
        if result.returncode != 0:
            log.error("curl error: rc=%d, stderr=%s", result.returncode, result.stderr[:200])
            raise HTTPException(
                status_code=502,
                detail=f"API call failed: {result.stderr[:200] or 'curl error'}",
            )
        data = json.loads(result.stdout)
        if "error" in data:
            err_msg = data["error"].get("message", str(data["error"]))[:200]
            log.error("API error: %s", err_msg)
            raise HTTPException(status_code=502, detail=f"API error: {err_msg}")
        content = data["choices"][0]["message"]["content"]

        # Kod bloğundan temizle ```python ... ```
        code = content.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            code = "\n".join(lines).strip()

        elapsed_ms = int((time.time() - start) * 1000)
        tokens = data.get("usage", {}).get("total_tokens", 0)

        log.info(
            "Generated code: qid=%d, fn=%s, %d chars, %d tokens, %dms",
            req.question_id, req.function_name, len(code), tokens, elapsed_ms,
        )

        return GenerateResponse(
            code=code, model=MAVIS_MODEL,
            tokens_used=tokens, elapsed_ms=elapsed_ms,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="API timeout (30s)")
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Generate failed")
        raise HTTPException(status_code=500, detail=f"Generate error: {e}")


# ═══════════════════════════════════════════════════════════════
# ─── 3) Üretilen kodu subprocess ile çalıştır ─────────────
# ═══════════════════════════════════════════════════════════════

def _run_single_test(code: str, fn_name: str, test_case: Dict) -> TestResult:
    """Tek test case'i çalıştır. Akıllı unpack (dict/list/primitive)."""
    test_input = test_case.get("input", test_case.get("args", []))
    expected = test_case.get("expected", test_case.get("output"))

    import json as _json
    input_json = _json.dumps(test_input)
    test_script = f"""
import sys
import json
import traceback

{code}

_input = json.loads({input_json!r})

# Akıllı çağrı:
# - dict ise: **kwargs
# - list ise: *args (fn tek parametre bekliyorsa) veya list olarak tek arg
# - primitive ise: doğrudan
try:
    if isinstance(_input, dict):
        result = {fn_name}(**_input)
    elif isinstance(_input, list):
        # Liste: *args ile unpack dene, hata olursa liste olarak tek arg
        try:
            result = {fn_name}(*_input)
        except TypeError:
            result = {fn_name}(_input)
    else:
        result = {fn_name}(_input)
    print(json.dumps({{"ok": True, "result": result}}))
except Exception as e:
    print(json.dumps({{"ok": False, "error": str(e), "trace": traceback.format_exc()}}))
"""
    try:
        proc = subprocess.run(
            ["python3", "-c", test_script],
            capture_output=True, text=True, timeout=EXEC_TIMEOUT,
            cwd=tempfile.gettempdir(),
        )
        if proc.returncode != 0:
            return TestResult(
                input=test_input, expected=expected, actual=None, passed=False,
                error=f"Runtime error: {proc.stderr[:200]}",
            )
        try:
            out = json.loads(proc.stdout.strip())
        except json.JSONDecodeError:
            return TestResult(
                input=test_input, expected=expected, actual=None, passed=False,
                error=f"Output parse error: {proc.stdout[:200]}",
            )
        if not out.get("ok"):
            return TestResult(
                input=test_input, expected=expected, actual=None, passed=False,
                error=out.get("error", "Unknown error"),
            )
        actual = out.get("result")
        return TestResult(
            input=test_input, expected=expected, actual=actual,
            passed=_deep_eq(actual, expected),
        )
    except subprocess.TimeoutExpired:
        return TestResult(
            input=test_input, expected=expected, actual=None, passed=False,
            error=f"Timeout ({EXEC_TIMEOUT}s)",
        )
    except Exception as e:
        return TestResult(
            input=test_input, expected=expected, actual=None, passed=False,
            error=str(e),
        )


def _deep_eq(a, b) -> bool:
    if a == b:
        return True
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-9
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(_deep_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a == b
    return False


@router.post("/run", response_model=RunResponse)
def run_code(req: RunRequest):
    """Üretilen kodu tüm test case'lerde çalıştır."""
    start = time.time()
    results: List[TestResult] = []
    stderr_all = ""

    for tc in req.test_cases:
        r = _run_single_test(req.code, req.function_name, tc)
        results.append(r)
        if not r.passed and r.error and "Runtime error" in r.error:
            stderr_all += r.error[:200] + "\n"

    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    elapsed_ms = int((time.time() - start) * 1000)

    return RunResponse(
        passed_count=passed_count, failed_count=failed_count,
        total=len(results), results=results,
        stderr=stderr_all[:500] if stderr_all else None,
        elapsed_ms=elapsed_ms,
    )


# ═══════════════════════════════════════════════════════════════
# ─── 4) Audit durumunu DB'ye yaz ───────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.post("/mark")
def mark_audited(req: MarkRequest):
    """DB'de is_audited, audit_status, audited_at güncelle."""
    sb = get_supabase_admin()
    try:
        update = {
            "is_audited": req.passed,
            "audit_status": "passed" if req.passed else "failed",
            "audited_at": "now()",
        }
        result = (
            sb.table("questions")
            .update(update)
            .eq("id", req.question_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Question {req.question_id} not found")
        log.info("Marked qid=%d as %s", req.question_id, "passed" if req.passed else "failed")
        return {
            "ok": True, "question_id": req.question_id,
            "is_audited": req.passed,
            "audit_status": "passed" if req.passed else "failed",
        }
    except HTTPException:
        raise
    except Exception as e:
        err_str = str(e)
        if "PGRST116" in err_str or "is_audited" in err_str or "Could not find" in err_str:
            log.error("Audit kolonları DB'de YOK! SQL migration gerekli.")
            raise HTTPException(
                status_code=503,
                detail="Audit kolonları DB'de yok. scripts/add_audit_columns.sql çalıştır, 5dk bekle.",
            )
        log.exception("Mark failed")
        raise HTTPException(status_code=500, detail=f"Mark error: {e}")


# ═══════════════════════════════════════════════════════════════
# ─── 5) Tek soru audit durumu ──────────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("/status/{question_id}", response_model=QuestionSummary)
def get_status(question_id: int):
    sb = get_supabase_admin()
    try:
        result = (
            sb.table("questions")
            .select("id, title, category, level, slug, is_audited, audit_status, audited_at, description, function_name, starter_code, test_cases")
            .eq("id", question_id)
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Not found")
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Status check failed")
        raise HTTPException(status_code=500, detail=f"Status error: {e}")


# ═══════════════════════════════════════════════════════════════
# ─── 6) Stats ──────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("/stats")
def audit_stats():
    sb = get_supabase_admin()
    try:
        result = sb.table("questions").select("audit_status").execute()
        rows = result.data or []
        stats = {"passed": 0, "failed": 0, "pending": 0}
        for r in rows:
            s = r.get("audit_status", "pending")
            stats[s] = stats.get(s, 0) + 1
        return {"total": len(rows), **stats}
    except Exception as e:
        log.exception("Stats failed")
        raise HTTPException(status_code=500, detail=f"Stats error: {e}")


# ═══════════════════════════════════════════════════════════════
# ─── 7) Debug: outbound network ────────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("/debug/network")
def debug_network():
    """Outbound network test — Railway DNS kısıtlarını debug et."""
    import socket
    hosts = [
        "api.openai.com", "generativelanguage.googleapis.com",
        "api.github.com", "api.minimax.io",
    ]
    results = {}
    for h in hosts:
        try:
            ip = socket.gethostbyname(h)
            results[h] = {"status": "ok", "ip": ip}
        except Exception as e:
            results[h] = {"status": "fail", "error": str(e)}
    # urllib test (API URL'sine gerçek istek)
    if MAVIS_API_KEY:
        url = MAVIS_API_BASE
        if not url.endswith("/chat/completions") and not url.endswith("/chatcompletion_v2"):
            url = f"{MAVIS_API_BASE}/chat/completions"
        try:
            body = json.dumps({
                "model": MAVIS_MODEL,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5,
            }).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers={
                "Authorization": f"Bearer {MAVIS_API_KEY}",
                "Content-Type": "application/json",
            })
            with urllib.request.urlopen(req, timeout=10) as r:
                body_text = r.read().decode("utf-8")
                results["urllib_api"] = {
                    "status": "ok",
                    "code": r.status,
                    "body_sample": body_text[:300],
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:300]
            results["urllib_api"] = {
                "status": "http_error",
                "code": e.code,
                "body_sample": err_body,
            }
        except Exception as e:
            results["urllib_api"] = {"status": "fail", "error": str(e)}
    # Model listesi (Gemini/OpenAI'da kullanılabilir modeller)
    models = None
    if MAVIS_API_KEY:
        try:
            models_url = MAVIS_API_BASE.rstrip("/")
            if models_url.endswith("/chat/completions"):
                models_url = models_url[:-len("/chat/completions")]
            models_url = f"{models_url}/models"
            req = urllib.request.Request(models_url, headers={
                "Authorization": f"Bearer {MAVIS_API_KEY}",
            })
            with urllib.request.urlopen(req, timeout=10) as r:
                models_data = json.loads(r.read().decode("utf-8"))
                if "data" in models_data:
                    models = [m.get("id") for m in models_data.get("data", [])][:20]
                elif "models" in models_data:
                    models = [m.get("name", "").split("/")[-1] for m in models_data.get("models", [])][:20]
        except Exception as e:
            models = f"error: {e}"

    return {
        "dns": results,
        "config": {
            "has_key": bool(MAVIS_API_KEY),
            "base": MAVIS_API_BASE,
            "model": MAVIS_MODEL,
        },
        "available_models": models,
    }


# ═══════════════════════════════════════════════════════════════
# ─── 8) BULK AUDIT: tüm pending soruları sırayla denetle ──
# ═══════════════════════════════════════════════════════════════

class BulkAuditResponse(BaseModel):
    total: int
    passed: int
    failed: int
    skipped: int
    errors: List[Dict[str, Any]] = []
    results: List[Dict[str, Any]] = []


@router.post("/bulk-audit", response_model=BulkAuditResponse)
async def bulk_audit(max_questions: int = 50):
    """Tüm pending soruları sırayla denetle.

    Her soru için:
      1) Mavis/OpenAI API ile kod üret
      2) Üretilen kodu test case'lerde çalıştır
      3) Hepsi geçtiyse DB'de is_audited=true işaretle

    max_questions: aynı anda kaç soru denetlensin (timeout önlemi)
    """
    if not MAVIS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="API key tanımlı değil.",
        )

    sb = get_supabase_admin()
    # Pending soruları al
    try:
        result = (
            sb.table("questions")
            .select("id, title, category, level, description, function_name, starter_code, test_cases, audit_status")
            .in_("audit_status", ["pending", "failed"])  # failed'lar da tekrar denetlenebilir
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

        if not description or not fn_name or not test_cases:
            skipped_count += 1
            errors.append({"id": qid, "title": title, "error": "Eksik alan (description/function_name/test_cases)"})
            continue

        # 1) Generate
        try:
            gen_req = GenerateRequest(
                question_id=qid,
                description=description,
                function_name=fn_name,
                test_cases=test_cases,
                starter_code=q.get("starter_code"),
            )
            gen_resp = await generate_code(gen_req)
            code = gen_resp.code
        except HTTPException as e:
            failed_count += 1
            errors.append({"id": qid, "title": title, "stage": "generate", "error": e.detail})
            continue
        except Exception as e:
            failed_count += 1
            errors.append({"id": qid, "title": title, "stage": "generate", "error": str(e)})
            continue

        # 2) Run tests
        try:
            run_req = RunRequest(
                question_id=qid, code=code, function_name=fn_name, test_cases=test_cases
            )
            run_resp = run_code(run_req)
        except Exception as e:
            failed_count += 1
            errors.append({"id": qid, "title": title, "stage": "run", "error": str(e)})
            continue

        # 3) Mark (all passed)
        all_passed = run_resp.passed_count == run_resp.total and run_resp.total > 0
        if all_passed:
            try:
                mark_audited(MarkRequest(question_id=qid, passed=True))
                passed_count += 1
                results.append({"id": qid, "title": title, "status": "passed", "tests": f"{run_resp.passed_count}/{run_resp.total}"})
            except Exception as e:
                errors.append({"id": qid, "title": title, "stage": "mark", "error": str(e)})
        else:
            failed_count += 1
            results.append({"id": qid, "title": title, "status": "failed", "tests": f"{run_resp.passed_count}/{run_resp.total}"})

    return BulkAuditResponse(
        total=len(questions),
        passed=passed_count,
        failed=failed_count,
        skipped=skipped_count,
        errors=errors[:20],  # max 20 error
        results=results,
    )
