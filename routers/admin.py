"""Admin endpointleri — minimal iskelet.

Sadece:
  • /admin/health              → basit health check
  • /admin/migrate/users-full  → KVKK uyumlu kullanıcı taşıma (eski → yeni Supabase)
  • /admin/migrate/report      → son taşıma raporu

Soru/tutorial/seed işlemleri artık scripts/ üzerinden yapılıyor.
Detay: scripts/seed_questions.py
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import os
import subprocess
import sys
import json

router = APIRouter(prefix="/admin", tags=["admin"])


# ═══════════════════════════════════════════════════════════════
# ─── Health ───────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("/health")
def health():
    """Liveness + DB bağlantı testi."""
    from supabase_client import get_supabase
    db_ok = False
    db_error = None
    try:
        sb = get_supabase()
        sb.table("questions").select("id").limit(1).execute()
        db_ok = True
    except Exception as e:
        db_error = str(e)
    return {
        "ok": True,
        "db_ok": db_ok,
        "db_error": db_error,
        "env": os.getenv("APP_ENV", "development"),
    }


# ═══════════════════════════════════════════════════════════════
# ─── KVKK Kullanıcı Taşıma ─────────────────────────────────
# ═══════════════════════════════════════════════════════════════

class FullMigrationRequest(BaseModel):
    dry_run: bool = True
    old_supabase_url: Optional[str] = None
    old_service_role_key: Optional[str] = None
    new_supabase_url: Optional[str] = None
    new_service_role_key: Optional[str] = None


@router.post("/migrate/users-full")
async def migrate_users_full(req: FullMigrationRequest, request: Request):
    """Tüm kullanıcı verisini eski Supabase'den yeni Supabase'ye taşı (KVKK Md. 12 log'lu).

    Service role key'ler body veya env'de olabilir.
    """
    admin_secret = os.getenv("ADMIN_SECRET", "")
    if not admin_secret or request.headers.get("X-Admin-Secret", "") != admin_secret:
        raise HTTPException(403, "admin yetkisi gerekli (X-Admin-Secret header)")

    env = os.environ.copy()
    env["DRY_RUN"] = "true" if req.dry_run else "false"
    env["OLD_SUPABASE_URL"] = req.old_supabase_url or env.get("OLD_SUPABASE_URL", "")
    env["OLD_SUPABASE_SERVICE_ROLE_KEY"] = (
        req.old_service_role_key or env.get("OLD_SUPABASE_SERVICE_ROLE_KEY", "")
    )
    env["NEW_SUPABASE_URL"] = req.new_supabase_url or env.get("NEW_SUPABASE_URL", "")
    env["NEW_SUPABASE_SERVICE_ROLE_KEY"] = (
        req.new_service_role_key or env.get("NEW_SUPABASE_SERVICE_ROLE_KEY", "")
    )

    missing = [k for k in [
        "OLD_SUPABASE_URL", "OLD_SUPABASE_SERVICE_ROLE_KEY",
        "NEW_SUPABASE_URL", "NEW_SUPABASE_SERVICE_ROLE_KEY",
    ] if not env.get(k)]
    if missing:
        raise HTTPException(400, f"Eksik env: {', '.join(missing)}")

    script_path = os.path.join(
        os.path.dirname(__file__), "..", "scripts", "migrate_users_full.py"
    )
    script_path = os.path.abspath(script_path)
    if not os.path.exists(script_path):
        raise HTTPException(500, f"Script yok: {script_path}")

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True, env=env, timeout=1800,
        )
        return {
            "ok": result.returncode == 0,
            "dry_run": req.dry_run,
            "exit_code": result.returncode,
            "stdout_tail": result.stdout[-3000:],
            "stderr_tail": result.stderr[-1500:],
            "report_path": "data/migration_report.json",
            "consent_log_path": "data/consent_log.jsonl",
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "30 dk timeout — script uzun sürdü")
    except Exception as e:
        raise HTTPException(500, f"subprocess error: {e}")


@router.get("/migrate/report")
async def get_migration_report(request: Request):
    """Son migration raporunu döndür."""
    admin_secret = os.getenv("ADMIN_SECRET", "")
    if not admin_secret or request.headers.get("X-Admin-Secret", "") != admin_secret:
        raise HTTPException(403, "admin yetkisi gerekli")
    report_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "migration_report.json"
    )
    if not os.path.exists(report_path):
        return {"ok": False, "message": "henüz rapor yok"}
    with open(report_path) as f:
        return {"ok": True, "report": json.load(f)}


# ═══════════════════════════════════════════════════════════════
# ─── Soru Üretimi (Mavis API) ────────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.post("/generate-questions")
async def generate_questions(request: Request):
    """Mavis API ile QUESTIONS-v3.py'ye yeni sorular üret + append.

    Query params:
      - count: 1-50 arası (default 20, eşit dağılım)
      - dry_run: true/false (default true — dosyaya yazmaz)

    Env gereksinimleri (Railway):
      - MINIMAX_API_KEY
      - MINIMAX_BASE_URL (opsiyonel)
      - MINIMAX_MODEL (opsiyonel)
    """
    admin_secret = os.getenv("ADMIN_SECRET", "")
    if not admin_secret or request.headers.get("X-Admin-Secret", "") != admin_secret:
        raise HTTPException(403, "admin yetkisi gerekli (X-Admin-Secret)")

    count = int(request.query_params.get("count", "20"))
    if count < 1 or count > 50:
        raise HTTPException(400, "count 1-50 arası olmalı")

    dry_run = request.query_params.get("dry_run", "true").lower() == "true"

    env = os.environ.copy()
    env["GENERATE_COUNT"] = str(count)
    env["DRY_RUN"] = "true" if dry_run else "false"

    if not env.get("MINIMAX_API_KEY"):
        raise HTTPException(400, "MINIMAX_API_KEY env tanımlı değil (Railway Variables)")

    script_path = os.path.join(
        os.path.dirname(__file__), "..", "scripts", "generate_questions.py"
    )
    if not os.path.exists(script_path):
        raise HTTPException(500, f"Script yok: {script_path}")

    log.warning(f"soru üretimi başlatıldı: count={count}, dry_run={dry_run}")

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True, env=env, timeout=600,  # 10 dk
        )
        return {
            "ok": result.returncode == 0,
            "count": count,
            "dry_run": dry_run,
            "exit_code": result.returncode,
            "stdout_tail": result.stdout[-3000:],
            "stderr_tail": result.stderr[-1500:],
            "next_step": (
                "dr_run=true ise aynı isteği dry_run=false ile tekrarla"
                if dry_run else
                "scripts/seed_questions.py ile DB'ye yaz"
            ),
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "10 dk timeout")
    except Exception as e:
        raise HTTPException(500, f"subprocess error: {e}")