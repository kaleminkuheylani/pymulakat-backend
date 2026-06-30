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


@router.post("/migrate/schema", response_model=MigrationResponse)
async def migrate_schema():
    """interwiews tablosuna yeni kolonları ekle (idempotent)."""
    import subprocess
    sql_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "migrate_schema.sql")
    sql_path = os.path.abspath(sql_path)

    if not os.path.exists(sql_path):
        raise HTTPException(404, f"SQL bulunamadı: {sql_path}")

    try:
        from supabase_client import get_service_role
        sb = get_service_role()

        with open(sql_path, "r") as f:
            sql_content = f.read()

        # SQL'i statement'lara böl ve her birini çalıştır
        statements = [s.strip() for s in sql_content.split(";") if s.strip() and not s.strip().startswith("--")]

        results = []
        for i, stmt in enumerate(statements):
            try:
                # rpc ile SQL çalıştır (PostgREST bunu desteklemiyor)
                # Alternatif: psycopg2 kullan
                results.append({"index": i, "stmt_preview": stmt[:80], "ok": True})
            except Exception as e:
                results.append({"index": i, "stmt_preview": stmt[:80], "ok": False, "error": str(e)})

        # psycopg2 ile direkt connection
        try:
            import psycopg2
            db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
            if db_url:
                conn = psycopg2.connect(db_url)
                conn.autocommit = True
                cur = conn.cursor()
                cur.execute(sql_content)
                cur.close()
                conn.close()
                return MigrationResponse(
                    ok=True,
                    message="Schema migration tamamlandı (psycopg2)",
                    details={"method": "psycopg2", "statements": len(statements)},
                )
        except ImportError:
            pass
        except Exception as e:
            return MigrationResponse(
                ok=False,
                message=f"psycopg2 hatası: {e}",
                details={"hint": "DATABASE_URL tanımlı mı? psycopg2 yüklü mü?"},
            )

        # Fallback: supabase rpc (exec_sql fonksiyonu gerekli)
        return MigrationResponse(
            ok=False,
            message="Schema migration için DATABASE_URL veya Supabase exec_sql gerekli",
            details={
                "hint": "Supabase Dashboard → SQL Editor'da migrate_schema.sql'i manuel çalıştır",
                "sql_file_path": sql_path,
            },
        )
    except Exception as e:
        return MigrationResponse(
            ok=False,
            message=f"Schema migration hatası: {e}",
            details={},
        )


@router.get("/health")
async def admin_health():
    """Admin endpoint sağlık kontrolü."""
    return {
        "ok": True,
        "supabase_url": os.getenv("SUPABASE_URL", "NOT SET"),
        "has_service_key": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY")),
    }