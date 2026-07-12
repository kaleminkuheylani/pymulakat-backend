"""Admin denetim endpointleri.

Soru açıklamasını al → Mavis API ile doğru kodu üret → çalıştır → test
geçerse DB'de is_audited=true olarak işaretle.

Endpointler:
  GET  /admin/audit/list            → tüm sorular (audit status ile)
  POST /admin/audit/generate        → Mavis API ile kod üret
  POST /admin/audit/run             → üretilen kodu subprocess ile çalıştır
  POST /admin/audit/mark            → DB'de is_audited update
  GET  /admin/audit/status/{id}     → tek soru audit durumu
"""

import os
import json
import logging
import subprocess
import tempfile
import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# httpx opsiyonel: Mavis API yoksa urllib ile fallback
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    import urllib.request

from supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/v2/admin/audit", tags=["admin-audit"])
log = logging.getLogger("pymulakat.audit")

# Mavis API config (OpenAI uyumlu)
MAVIS_API_KEY = os.environ.get("MAVIS_API_KEY", "")
MAVIS_API_BASE = os.environ.get("MAVIS_API_BASE", "https://api.mavis.com/v1")
MAVIS_MODEL = os.environ.get("MAVIS_MODEL", "mavis-code")

# Code execution timeout (saniye)
EXEC_TIMEOUT = 8


# ═══════════════════════════════════════════════════════════════
# ─── Pydantic Models ─────────────────────────────────────────
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
# ─── 1) Soru listesi (audit status) ───────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("/list", response_model=List[QuestionSummary])
def list_questions():
    """Tüm soruları audit durumu ile döndür (scrollable dropdown için).

    Kolonlar (is_audited, audit_status, audited_at) henüz eklenmediyse
    fallback: temel soru verisi + audit_status="pending" default.
    """
    sb = get_supabase_admin()
    # Önce audit kolonları dahil SELECT dene
    try:
        result = (
            sb.table("questions")
            .select("id, title, category, level, slug, is_audited, audit_status, audited_at, description, function_name, starter_code, test_cases")
            .order("id", desc=False)
            .execute()
        )
        return result.data or []
    except Exception as e1:
        # Audit kolonları yoksa (404/PGRST116) fallback
        err_str = str(e1)
        if "PGRST116" in err_str or "is_audited" in err_str or "404" in err_str or "Could not find" in err_str:
            log.warning("Audit kolonları yok, fallback temel sorgu (DB migration gerekli)")
            try:
                result = (
                    sb.table("questions")
                    .select("id, title, category, level, slug, description, function_name, starter_code, test_cases")
                    .order("id", desc=False)
                    .execute()
                )
                rows = result.data or []
                # Default audit alanları ekle
                for r in rows:
                    r["is_audited"] = False
                    r["audit_status"] = "pending"
                    r["audited_at"] = None
                return rows
            except Exception as e2:
                log.exception("Fallback list failed")
                raise HTTPException(status_code=500, detail=f"List error (fallback): {e2}")
        log.exception("List questions failed")
        raise HTTPException(status_code=500, detail=f"List error: {e1}")


# ═══════════════════════════════════════════════════════════════
# ─── 2) Mavis API ile kod üret ───────────────────────────────
# ═══════════════════════════════════════════════════════════════

def _build_prompt(req: GenerateRequest) -> str:
    """Mavis API için prompt oluştur."""
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
4. Kısa yol fonksiyonları YASAK (sorted, set, Counter, defaultdict, bisect, heapq)
5. Sadece saf Python (built-in) kullan
6. Test case'lerdeki tüm senaryoları karşıla

Sadece Python kodunu döndür (açıklama yok, sadece kod):
```python
def {req.function_name}(...):
    ...
```"""


@router.post("/generate", response_model=GenerateResponse)
async def generate_code(req: GenerateRequest):
    """Mavis API ile doğru kodu üret."""
    if not MAVIS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="MAVIS_API_KEY env tanımlı değil (Railway). Mavis API devre dışı.",
        )

    prompt = _build_prompt(req)
    start = time.time()

    if not HTTPX_AVAILABLE:
        # urllib fallback (sync)
        body = json.dumps({
            "model": MAVIS_MODEL,
            "messages": [
                {"role": "system", "content": "Sen deneyimli Python yazılımcısı."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1500,
        }).encode("utf-8")
        req_obj = urllib.request.Request(
            f"{MAVIS_API_BASE}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {MAVIS_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req_obj, timeout=30) as resp:
            response_text = resp.read().decode("utf-8")
            data = json.loads(response_text)
        content = data["choices"][0]["message"]["content"]
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
        return GenerateResponse(
            code=code, model=MAVIS_MODEL,
            tokens_used=tokens, elapsed_ms=elapsed_ms,
        )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{MAVIS_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {MAVIS_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
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
                },
            )

        if response.status_code != 200:
            log.error("Mavis API error: %s — %s", response.status_code, response.text[:300])
            raise HTTPException(
                status_code=502,
                detail=f"Mavis API error: {response.status_code} — {response.text[:200]}",
            )

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        # Kod bloğundan temizle ```python ... ```
        code = content.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            # İlk satır ```python veya ```
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Son satır ```
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
            code=code,
            model=MAVIS_MODEL,
            tokens_used=tokens,
            elapsed_ms=elapsed_ms,
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Mavis API timeout (30s)")
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Generate failed")
        raise HTTPException(status_code=500, detail=f"Generate error: {e}")


# ═══════════════════════════════════════════════════════════════
# ─── 3) Üretilen kodu subprocess ile çalıştır ────────────────
# ═══════════════════════════════════════════════════════════════

def _run_test(code: str, fn_name: str, test_case: Dict) -> TestResult:
    """Tek test case'i çalıştır."""
    # Test case'ten input/expected al
    inp = test_case.get("input", test_case.get("args", []))
    expected = test_case.get("expected", test_case.get("output"))

    # input dict ise kwargs olarak aç
    if isinstance(inp, dict):
        args = []
        kwargs = inp
    elif isinstance(inp, list):
        args = inp
        kwargs = {}
    else:
        args = [inp]
        kwargs = {}

    # Test runner script oluştur
    test_script = f"""
import sys
import json
import traceback

# User kodu
{code}

# Test
_args = json.loads({json.dumps(json.dumps(args))})
_kwargs = json.loads({json.dumps(json.dumps(kwargs))})

try:
    result = {_qualname(fn_name)}(*_args, **_kwargs)
    print(json.dumps({{"ok": True, "result": result}}))
except Exception as e:
    print(json.dumps({{"ok": False, "error": str(e), "trace": traceback.format_exc()}}))
"""
    return _test_script, _args, _kwargs, expected


def _qualname(fn_name: str) -> str:
    return fn_name


@router.post("/run", response_model=RunResponse)
def run_code(req: RunRequest):
    """Üretilen kodu tüm test case'lerde çalıştır."""
    start = time.time()
    results: List[TestResult] = []
    stderr_all = ""

    for tc in req.test_cases:
        try:
            test_script, args, kwargs, expected = _run_test(
                req.code, req.function_name, tc
            )
            # subprocess çalıştır
            proc = subprocess.run(
                ["python3", "-c", test_script],
                capture_output=True,
                text=True,
                timeout=EXEC_TIMEOUT,
                cwd=tempfile.gettempdir(),
            )
            stderr_all += proc.stderr[:200] + "\n" if proc.stderr else ""

            if proc.returncode != 0:
                results.append(TestResult(
                    input=tc.get("input"),
                    expected=expected,
                    actual=None,
                    passed=False,
                    error=f"Runtime error: {proc.stderr[:200]}",
                ))
                continue

            # Parse output
            try:
                out = json.loads(proc.stdout.strip())
            except json.JSONDecodeError:
                results.append(TestResult(
                    input=tc.get("input"),
                    expected=expected,
                    actual=None,
                    passed=False,
                    error=f"Output parse error: {proc.stdout[:200]}",
                ))
                continue

            if not out.get("ok"):
                results.append(TestResult(
                    input=tc.get("input"),
                    expected=expected,
                    actual=None,
                    passed=False,
                    error=out.get("error", "Unknown error"),
                ))
                continue

            actual = out.get("result")
            # Karşılaştır (deep equality)
            passed = _deep_eq(actual, expected)
            results.append(TestResult(
                input=tc.get("input"),
                expected=expected,
                actual=actual,
                passed=passed,
            ))
        except subprocess.TimeoutExpired:
            results.append(TestResult(
                input=tc.get("input"),
                expected=expected,
                actual=None,
                passed=False,
                error=f"Timeout ({EXEC_TIMEOUT}s)",
            ))
        except Exception as e:
            results.append(TestResult(
                input=tc.get("input"),
                expected=expected,
                actual=None,
                passed=False,
                error=str(e),
            ))

    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    elapsed_ms = int((time.time() - start) * 1000)

    return RunResponse(
        passed_count=passed_count,
        failed_count=failed_count,
        total=len(results),
        results=results,
        stderr=stderr_all[:500] if stderr_all else None,
        elapsed_ms=elapsed_ms,
    )


def _deep_eq(a, b) -> bool:
    """Deep equality (list, dict, primitive)."""
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


# ═══════════════════════════════════════════════════════════════
# ─── 4) Audit durumunu DB'ye yaz ─────────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.post("/mark")
def mark_audited(req: MarkRequest):
    """DB'de is_audited, audit_status, audited_at güncelle.

    Audit kolonları henüz DB'de yoksa 503 doner (migration gerekli).
    """
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
            raise HTTPException(
                status_code=404,
                detail=f"Question {req.question_id} not found",
            )
        log.info(
            "Marked qid=%d as %s",
            req.question_id,
            "passed" if req.passed else "failed",
        )
        return {
            "ok": True,
            "question_id": req.question_id,
            "is_audited": req.passed,
            "audit_status": "passed" if req.passed else "failed",
        }
    except HTTPException:
        raise
    except Exception as e:
        err_str = str(e)
        if "PGRST116" in err_str or "is_audited" in err_str or "Could not find" in err_str:
            log.error(
                "Audit kolonlari DB'de YOK! Supabase SQL Editor'de "
                "scripts/add_audit_columns.sql calistir, sonra 5dk bekle "
                "(PostgREST schema cache)."
            )
            raise HTTPException(
                status_code=503,
                detail=(
                    "Audit kolonlari DB'de yok. Supabase SQL Editor'de "
                    "scripts/add_audit_columns.sql calistir, sonra 5dk bekle."
                ),
            )
        log.exception("Mark failed")
        raise HTTPException(status_code=500, detail=f"Mark error: {e}")


# ═══════════════════════════════════════════════════════════════
# ─── 5) Tek soru audit durumu ─────────────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("/status/{question_id}", response_model=QuestionSummary)
def get_status(question_id: int):
    """Tek sorunun audit durumunu getir."""
    sb = get_supabase_admin()
    try:
        result = (
            sb.table("questions")
            .select("id, title, category, level, slug, is_audited, audit_status, audited_at")
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
# ─── 6) Toplu test (tüm pending soruları) ───────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("/stats")
def audit_stats():
    """Audit durumu özeti (dashboard)."""
    sb = get_supabase_admin()
    try:
        result = (
            sb.table("questions")
            .select("audit_status")
            .execute()
        )
        rows = result.data or []
        stats = {"passed": 0, "failed": 0, "pending": 0}
        for r in rows:
            s = r.get("audit_status", "pending")
            stats[s] = stats.get(s, 0) + 1
        return {"total": len(rows), **stats}
    except Exception as e:
        log.exception("Stats failed")
        raise HTTPException(status_code=500, detail=f"Stats error: {e}")
