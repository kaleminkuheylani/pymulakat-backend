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
from pathlib import Path
import subprocess
import sys
import json
import logging

router = APIRouter(prefix="/api/v2/admin", tags=["admin"])
log = logging.getLogger("pymulakat.admin")

# Audit endpoints (import edip router'a ekle)
import sys
import traceback
try:
    from routers.audit import router as audit_router
    router.include_router(audit_router)
    log.info("✅ audit endpoints yüklendi (Mavis API + test runner)")
    print(f"✅ audit_router.routes: {[r.path for r in audit_router.routes]}", file=sys.stderr)
except Exception as e:
    err_msg = f"❌ audit router yüklenemedi: {e}"
    log.exception(err_msg)
    print(err_msg, file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)


# ═══════════════════════════════════════════════════════════════
# ─── Health ───────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("/health")
def health():
    """Liveness + DB bağlantı testi."""
    from supabase_client import get_supabase
    db_ok = False
    db_error = None
    db_stats = {}
    try:
        sb = get_supabase()
        sb.table("questions").select("id").limit(1).execute()
        db_ok = True
        # Detaylı sayım (debug için)
        try:
            total = sb.table("questions").select("id", count="exact").execute()
            db_stats["total"] = total.count
        except Exception:
            pass
        try:
            active = sb.table("questions").select("id", count="exact").eq("is_published", True).execute()
            db_stats["is_published_true"] = active.count
        except Exception as e:
            db_stats["is_published_error"] = str(e)[:200]
    except Exception as e:
        db_error = str(e)
    return {
        "ok": True,
        "db_ok": db_ok,
        "db_error": db_error,
        "db_stats": db_stats,
        "supabase_url": os.getenv("SUPABASE_URL", "(unset)"),
        "env": os.getenv("APP_ENV", "development"),
    }


@router.post("/invalidate-cache")
async def invalidate_cache_endpoint(request: Request):
    """In-process soru cache'i sıfırla (DB update'ten sonra).

    60 saniye cache'i beklemek istemiyorsan bunu çağır.
    """
    admin_secret = os.getenv("ADMIN_SECRET", "")
    if not admin_secret or request.headers.get("X-Admin-Secret", "") != admin_secret:
        raise HTTPException(403, "admin yetkisi gerekli (X-Admin-Secret header)")
    try:
        from question_loader import invalidate_cache
        invalidate_cache()
        return {"ok": True, "message": "Cache sıfırlandı. Sonraki istek DB'den fresh çeker."}
    except Exception as e:
        raise HTTPException(500, f"cache invalidate hata: {e}")


# ═══════════════════════════════════════════════════════════════
# ─── Soru Seed (DB ilk doldurma) ────────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.post("/seed-questions")
async def seed_questions_endpoint(request: Request):
    """CSV'den DB 'questions' tablosuna inline yazma (parametresiz).

    CSV'den sadece şu alanlar yazılır:
      - description, starter_code, test_cases, hints,
      - function_name, title, level, category
    Diğer kolonlar (slug, meta_*, related_question_ids, related_concepts, tags,
    topic, tutorial_slug, complexity, explanation, meta_title, meta_description,
    meta_keywords) DB-side YÖNETİLİR ve korunur.

    id → legacy_id olarak yazılır (DB'de primary key değişmez, upload edilen
    sorular orijinal id'lerini taşımaya devam eder).

    DB'de aynı legacy_id yoksa satır INSERT edilir; varsa UPDATE.
    Endpoint idempotent: tekrar tekrar çağrılabilir.

    Headers: X-Admin-Secret (= ADMIN_SECRET env)
    """
    admin_secret = os.getenv("ADMIN_SECRET", "")
    if not admin_secret or request.headers.get("X-Admin-Secret", "") != admin_secret:
        raise HTTPException(403, "admin yetkisi gerekli (X-Admin-Secret header)")

    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        raise HTTPException(400, "Supabase env (SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY) tanımlı değil")

    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "QUESTIONS-v3.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(500, f"CSV yok: {csv_path}")

    csv_only_fields = (
        "description", "starter_code", "test_cases", "hints",
        "function_name", "title", "level", "category",
    )

    import csv as _csv
    rows_to_write = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = _csv.DictReader(f)
        for row in reader:
            raw_id = row.get("id", "").strip()
            if not raw_id:
                continue
            try:
                legacy_id = int(raw_id)
            except ValueError:
                continue
            payload = {"legacy_id": legacy_id}
            for fld in csv_only_fields:
                val = row.get(fld, "")
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                payload[fld] = val.replace('""', '"')
            rows_to_write.append(payload)

    from supabase_client import get_supabase
    sb = get_supabase()

    succeeded = []
    failed = []
    for payload in rows_to_write:
        lid = payload["legacy_id"]
        try:
            result = (
                sb.table("questions")
                .upsert(payload, on_conflict="legacy_id")
                .execute()
            )
            if result.data:
                succeeded.append(lid)
            else:
                failed.append({"legacy_id": lid, "reason": "no row upserted"})
        except Exception as e:
            failed.append({"legacy_id": lid, "reason": str(e)[:200]})

    log.warning(f"seed-questions: {len(succeeded)}/{len(rows_to_write)} upserted")

    return {
        "ok": True,
        "rows_planned": len(rows_to_write),
        "upserted": len(succeeded),
        "failed": len(failed),
        "failed_detail": failed[:20],
        "csv_fields_written": list(csv_only_fields),
        "preserved_db_fields": [
            "slug", "complexity", "explanation", "meta_title",
            "meta_description", "meta_keywords", "related_concepts",
            "related_question_ids", "tags", "topic", "tutorial_slug",
        ],
        "next_step": "/admin/invalidate-cache çağırıp cache temizle, sonra /api/v2/questions/{id} ile doğrula",
    }


# (dry-run shortcut kaldırıldı: parametresiz, idempotent endpoint yeterli)
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

    Body (opsiyonel):
      - category: tek bir kategori için sadece üretim ("pandas" gibi)

    Env gereksinimleri (Railway):
      - MINIMAX_API_KEY
      - MINIMAX_BASE_URL (opsiyonel)
      - MINIMAX_MODEL (opsiyonel)

    Not: generate_questions.py'yi değil, halefi question_generator.py'yi çağırır.
    """
    admin_secret = os.getenv("ADMIN_SECRET", "")
    if not admin_secret or request.headers.get("X-Admin-Secret", "") != admin_secret:
        raise HTTPException(403, "admin yetkisi gerekli (X-Admin-Secret)")

    count = int(request.query_params.get("count", "20"))
    if count < 1 or count > 50:
        raise HTTPException(400, "count 1-50 arası olmalı")

    dry_run = request.query_params.get("dry_run", "true").lower() == "true"

    try:
        body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    except Exception:
        body = {}
    category = body.get("category") if isinstance(body, dict) else None

    env = os.environ.copy()
    env["GENERATE_COUNT"] = str(count)
    env["DRY_RUN"] = "true" if dry_run else "false"

    if not env.get("MINIMAX_API_KEY"):
        raise HTTPException(400, "MINIMAX_API_KEY env tanımlı değil (Railway Variables)")

    script_path = os.path.join(
        os.path.dirname(__file__), "..", "scripts", "question_generator.py"
    )
    if not os.path.exists(script_path):
        raise HTTPException(500, f"Script yok: {script_path}")

    log.warning(f"soru üretimi başlatıldı: count={count}, dry_run={dry_run}, category={category}")

    cmd = [sys.executable, script_path]
    proc_env = env.copy()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, env=proc_env, timeout=600,  # 10 dk
        )
        return {
            "ok": result.returncode == 0,
            "count": count,
            "dry_run": dry_run,
            "category": category,
            "script": "question_generator.py",
            "exit_code": result.returncode,
            "stdout_tail": result.stdout[-3000:],
            "stderr_tail": result.stderr[-1500:],
            "next_step": (
                "dry_run=true ise aynı isteği dry_run=false ile tekrarla"
                if dry_run else
                "scripts/seed_questions.py ile DB'ye yaz"
            ),
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "10 dk timeout")
    except Exception as e:
        raise HTTPException(500, f"subprocess error: {e}")

# ═══════════════════════════════════════════════════════════════
# ─── BULK UPSERT: data/QUESTIONS-v3.csv → Supabase ───────────
# ═══════════════════════════════════════════════════════════════

class BulkSeedResponse(BaseModel):
    total: int
    inserted: int
    updated: int
    failed: int
    errors: List[Dict[str, Any]] = []


@router.post("/bulk-seed-questions")
def bulk_seed_questions():
    """data/QUESTIONS-v3.csv dosyasını oku, Supabase'e upsert et.

    - id varsa: UPDATE (slug, title, description, function_name, starter_code, test_cases, hints, level, category)
    - id yoksa: INSERT
    - Multi-line CSV alanları Python csv modülü ile doğru parse edilir
    """
    import csv
    sb = get_supabase_admin()

    csv_paths = [
        "data/QUESTIONS-v3.csv",                # local
        "/app/data/QUESTIONS-v3.csv",            # Railway
    ]
    csv_path = None
    for p in csv_paths:
        if Path(p).exists():
            csv_path = p
            break
    if not csv_path:
        raise HTTPException(status_code=404, detail="QUESTIONS-v3.csv not found")

    inserted = 0
    updated = 0
    failed = 0
    errors = []

    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                sid = int(row.get("id", "0"))
                if not sid:
                    continue
                # Upsert data
                data = {
                    "category": row.get("category", ""),
                    "title": row.get("title", ""),
                    "slug": row.get("slug", ""),
                    "level": row.get("level", "beginner"),
                    "description": row.get("description", ""),
                    "function_name": row.get("function_name", ""),
                    "starter_code": row.get("starter_code", ""),
                    "test_cases": row.get("test_cases", ""),  # JSON string
                    "hints": row.get("hints", ""),  # JSON string
                }
                # test_cases ve hints JSON string olmalı
                # Supabase jsonb alana insert ederken Python list/dict gönderilebilir
                # ama burada string olarak bırakıyoruz, DB'de jsonb/text ne ise o olur
                # Mevcut data_type: Supabase'te jsonb olabilir veya text
                # Text olarak insert edip, okurken parse ederiz
                result = sb.table("questions").upsert(
                    {**data, "id": sid},
                    on_conflict="id",
                ).execute()
                if result.data:
                    if len(result.data) == 1 and result.data[0].get("id") == sid:
                        # upsert hem insert hem update destekler, ayırt etmek zor
                        inserted += 1
            except Exception as e:
                failed += 1
                errors.append({"id": row.get("id", "?"), "error": str(e)[:200]})
                if len(errors) < 5:
                    log.exception("Upsert failed for id=%s", row.get("id", "?"))

    return BulkSeedResponse(
        total=inserted + failed,
        inserted=inserted,
        updated=updated,
        failed=failed,
        errors=errors,
    )
