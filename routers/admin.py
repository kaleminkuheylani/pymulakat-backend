"""Geçici admin endpointleri — migration ve bakım için.

⚠️ PRODUCTION'DA KULLANIRKEN DİKKATLİ OL!
Bu endpoint migration çalıştırır, DB'ye büyük INSERT/UPDATE yapar.
Sadece ilk kurulumda veya veri güncellemesinde kullanılmalı.

Kullanım:
    curl -X POST https://pymulakat-backend-production.up.railway.app/admin/migrate/questions
    curl -X POST https://pymulakat-backend-production.up.railway.app/admin/migrate/tutorials
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import sys

router = APIRouter(prefix="/admin", tags=["admin"])


class MigrationResponse(BaseModel):
    ok: bool
    message: str
    details: dict = {}


def _run_script(script_name: str) -> dict:
    """Bir Python script'i subprocess olarak çalıştır."""
    import subprocess
    script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", script_name)
    script_path = os.path.abspath(script_path)

    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script bulunamadı: {script_path}")

    # Env'i forward et
    env = os.environ.copy()

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            env=env,
            timeout=300,  # 5 dakika timeout
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout[-3000:],  # Son 3000 char
            "stderr": result.stderr[-1000:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "error": "Migration 300 saniyede tamamlanmadı"}
    except Exception as e:
        return {"exit_code": -1, "error": str(e)}


@router.post("/migrate/questions", response_model=MigrationResponse)
async def migrate_questions():
    """QUESTIONS.py + SEO_CONTENT'i Supabase 'interwiews' tablosuna migrate et."""
    result = _run_script("migrate_questions.py")
    return MigrationResponse(
        ok=result.get("exit_code") == 0,
        message="Migration tamamlandı" if result.get("exit_code") == 0 else "Migration başarısız",
        details=result,
    )


@router.post("/migrate/tutorials", response_model=MigrationResponse)
async def migrate_tutorials():
    """7 fallback tutorial'ı 'tutorials' tablosuna migrate et."""
    result = _run_script("migrate_tutorials.py")
    return MigrationResponse(
        ok=result.get("exit_code") == 0,
        message="Migration tamamlandı" if result.get("exit_code") == 0 else "Migration başarısız",
        details=result,
    )


@router.get("/health")
async def admin_health():
    """Admin endpoint sağlık kontrolü."""
    return {
        "ok": True,
        "supabase_url": os.getenv("SUPABASE_URL", "NOT SET"),
        "has_service_key": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY")),
    }