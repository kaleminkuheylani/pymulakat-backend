print("DEPLOY TRIGGER 2026-07-12")
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
from typing import Optional, List, Dict, Any
import os
from pathlib import Path
import subprocess
import sys
import json
import logging
from supabase_client import get_supabase, get_supabase_admin
import traceback
import csv

router = APIRouter(prefix="/api/v2/admin", tags=["admin"])
log = logging.getLogger("pymulakat.admin")

# Audit endpoints (import edip router'a ekle)
try:
    from routers.audit import router as audit_router
    router.include_router(audit_router)
    log.info("✅ audit endpoints yüklendi (Mavis API + test runner)")
except Exception as e:
    log.exception(f"❌ audit router yüklenemedi: {e}")
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
    from supabase_client import get_supabase  # get_supabase_admin zaten modül seviyesinde
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

    from supabase_client import get_supabase  # get_supabase_admin zaten modül seviyesinde
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
# ═══════════════════════════════════════════════════════════════@router.post("/bulk-seed-test")
def bulk_seed_test():
    """Hata ayiklama: CSV oku, JSON parse et."""
    try:
        csv_path = "data/QUESTIONS-v3.csv"
        if not Path(csv_path).exists():
            csv_path = "/app/data/QUESTIONS-v3.csv"
        if not Path(csv_path).exists():
            return {"error": "CSV yok", "paths_checked": ["data/QUESTIONS-v3.csv", "/app/data/QUESTIONS-v3.csv"]}
        
        # Sadece ilk 3 satırı oku
        results = {"csv_path": csv_path, "rows": []}
        with open(csv_path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 3:
                    break
                sid = row.get("id", "?")
                results["rows"].append({
                    "id": sid,
                    "title": row.get("title", "")[:50],
                    "test_cases_len": len(row.get("test_cases", "")),
                    "hints_len": len(row.get("hints", "")),
                })
        return results
    except Exception as e:
        log.exception("bulk-seed-test failed")
        return {"error": str(e)[:500]}

class BulkSeedResponse(BaseModel):
    total: int
    inserted: int
    updated: int
    failed: int
    errors: List[Dict[str, Any]] = []


@router.post("/bulk-seed-questions")
def bulk_seed_questions(batch_size: int = 20):
    """data/QUESTIONS-v3.csv -> Supabase batch upsert (PostgREST 42601 icin)."""
    sb = get_supabase_admin()

    csv_paths = ["data/QUESTIONS-v3.csv", "/app/data/QUESTIONS-v3.csv"]
    csv_path = None
    for p_path in csv_paths:
        if Path(p_path).exists():
            csv_path = p_path
            break
    if not csv_path:
        raise HTTPException(status_code=404, detail="QUESTIONS-v3.csv not found")

    # Once CSV'yi oku ve parse et
    rows = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = int(row.get("id", "0") or 0)
            if not sid:
                continue
            tc_raw = row.get("test_cases", "[]")
            hints_raw = row.get("hints", "[]")
            try:
                test_cases = json.loads(tc_raw) if tc_raw.startswith("[") else tc_raw
            except Exception:
                test_cases = tc_raw
            try:
                hints = json.loads(hints_raw) if hints_raw.startswith("[") else hints_raw
            except Exception:
                hints = hints_raw

            rows.append({
                "id": sid,
                "category": row.get("category", ""),
                "title": row.get("title", ""),
                "slug": row.get("slug", ""),
                "level": row.get("level", "beginner"),
                "description": row.get("description", ""),
                "function_name": row.get("function_name", ""),
                "starter_code": row.get("starter_code", ""),
                "test_cases": test_cases,
                "hints": hints,
            })

    inserted = 0
    failed = 0
    errors = []

    # Batch'li upsert (PostgREST 42601: payload too large)
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        try:
            # upsert batch
            result = sb.table("questions").upsert(
                batch, on_conflict="id"
            ).execute()
            if result.data:
                inserted += len(result.data)
        except Exception as e:
            err_msg = str(e)[:500]
            log.exception(f"Batch {i}-{i+batch_size} upsert FAIL (satir basina fallback): {err_msg}")
            for row in batch:
                try:
                    sb.table("questions").upsert(
                        [row], on_conflict="id"
                    ).execute()
                    inserted += 1
                except Exception as e2:
                    failed += 1
                    errors.append({"id": row["id"], "error": str(e2)[:200]})
                    if len(errors) < 10:
                        log.exception("Row upsert failed for id=%s", row["id"])

    return BulkSeedResponse(
        total=inserted + failed,
        inserted=inserted,
        updated=0,
        failed=failed,
        errors=errors,
    )

class BulkSeedRowResult(BaseModel):
    id: int
    status: str
    error: str = ""


class BulkSeedResponse(BaseModel):
    total: int
    inserted: int
    failed: int
    rows: List[BulkSeedRowResult] = []


@router.post("/bulk-seed-questions")
def bulk_seed_questions():
    """data/QUESTIONS-v3.csv -> Supabase tek tek upsert (detayli hata)."""
    sb = get_supabase_admin()

    csv_paths = ["data/QUESTIONS-v3.csv", "/app/data/QUESTIONS-v3.csv"]
    csv_path = None
    for p_path in csv_paths:
        if Path(p_path).exists():
            csv_path = p_path
            break
    if not csv_path:
        raise HTTPException(status_code=404, detail="QUESTIONS-v3.csv not found")

    rows_result = []
    inserted = 0
    failed = 0

    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            sid_str = row.get("id", "0")
            try:
                sid = int(sid_str)
            except Exception:
                rows_result.append(BulkSeedRowResult(id=0, status="skip", error="bad id"))
                continue

            # JSON fields parse
            tc_raw = row.get("test_cases", "[]") or "[]"
            hints_raw = row.get("hints", "[]") or "[]"
            try:
                test_cases = json.loads(tc_raw) if tc_raw.startswith("[") else tc_raw
            except Exception:
                test_cases = []
            try:
                hints = json.loads(hints_raw) if hints_raw.startswith("[") else hints_raw
            except Exception:
                hints = []

            data = {
                "id": sid,
                "category": row.get("category", "") or "",
                "title": row.get("title", "") or "",
                "slug": row.get("slug", "") or "",
                "level": row.get("level", "beginner") or "beginner",
                "description": row.get("description", "") or "",
                "function_name": row.get("function_name", "") or "",
                "starter_code": row.get("starter_code", "") or "",
                "test_cases": test_cases,
                "hints": hints,
            }
            # Default audit fields (yoksa)
            try:
                # Önce UPDATE dene (id varsa)
                existing = sb.table("questions").select("id").eq("id", sid).execute()
                if existing.data:
                    # id'yi data'dan çıkar update için
                    update_data = {k: v for k, v in data.items() if k != "id"}
                    sb.table("questions").update(update_data).eq("id", sid).execute()
                else:
                    sb.table("questions").insert(data).execute()
                inserted += 1
                rows_result.append(BulkSeedRowResult(id=sid, status="ok"))
            except Exception as e:
                failed += 1
                err = str(e)[:200]
                rows_result.append(BulkSeedRowResult(id=sid, status="fail", error=err))
                if failed < 5:
                    log.exception("Upsert failed for id=%s", sid)

    return BulkSeedResponse(
        total=inserted + failed,
        inserted=inserted,
        failed=failed,
        rows=rows_result,
    )


@router.post("/delete-pending-questions")
def delete_pending_questions():
    """audit_status = 'pending' olan tüm sorulari DB'den sil."""
    sb = get_supabase_admin()
    try:
        result = sb.table("questions").delete().eq("audit_status", "pending").execute()
        deleted = len(result.data) if result.data else 0
        return {"deleted": deleted}
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")



# ═══════════════════════════════════════════════════════════════
# ─── User role management (Supabase admin) ───────────────────
# ═══════════════════════════════════════════════════════════════

class SetRoleRequest(BaseModel):
    role: str  # "admin" | "user"


@router.get("/users/list")
def list_admin_users(limit: int = 50):
    """Tum auth.users listele (admin kontrolu gerekli - sadece super admin).
    
    Sadece admin olan user'lar bu endpoint'i kullanabilir.
    NOT: Bu endpoint ileride super_admin check eklenmeli.
    Simdilik service_role ile auth.users.admin API kullanir.
    """
    sb = get_supabase_admin()
    try:
        # Supabase Admin API: GET /auth/v1/admin/users
        # service_role key ile
        result = sb.auth.admin.list_users(page=1, per_page=limit)
        users = []
        for u in result:
            app_meta = u.app_metadata or {}
            users.append({
                "id": u.id,
                "email": u.email,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_sign_in_at": u.last_sign_in_at.isoformat() if u.last_sign_in_at else None,
                "role": app_meta.get("role", "user"),
                "provider": app_meta.get("provider", "email"),
                "email_confirmed": bool(u.email_confirmed_at),
            })
        return {"users": users, "total": len(users)}
    except Exception as e:
        raise HTTPException(500, f"List users failed: {e}")


@router.post("/users/{user_id}/set-role")
def set_user_role(user_id: str, req: SetRoleRequest):
    """User'in app_metadata.role'unu guncelle (service_role ile).
    
    SADECE Supabase auth admin yapabilir. Bu endpoint zaten admin-only
    (UI'da requireAdmin ile korunuyor). Super admin check ileride eklenir.
    """
    if req.role not in ("admin", "user"):
        raise HTTPException(400, "role 'admin' veya 'user' olmali")
    
    sb = get_supabase_admin()
    try:
        # Mevcut user'i al
        user_result = sb.auth.admin.get_user_by_id(user_id)
        if not user_result:
            raise HTTPException(404, "User bulunamadi")
        
        current_meta = dict(user_result.app_metadata or {})
        current_meta["role"] = req.role
        current_meta["role_updated_at"] = "2026-07-12T18:15:00Z"
        
        # app_metadata guncelle
        result = sb.auth.admin.update_user_by_id(
            user_id,
            {"app_metadata": current_meta}
        )
        return {
            "id": result.user.id,
            "email": result.user.email,
            "role": current_meta["role"],
            "updated": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Set role failed: {e}")


@router.get("/users/me")
def get_current_user_info(request: Request):
    """Token veya Supabase cookie'den user bilgisi (debug + admin guard icin).
    
    Frontend admin guard bu endpoint'i "fresh role" kontrolu icin cagirir
    (Supabase JWT cache'li olabilir, logout-login sonrasi bile).
    """
    import base64
    import json
    
    token = ""
    
    # 1) Authorization header (Bearer)
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
    
    # 2) Supabase cookie'lerden access_token cek
    if not token:
        cookies = request.cookies
        for name, value in cookies.items():
            if name.endswith("-auth-token") and value:
                # Supabase cookie base64url encoded JSON
                # Bazen chunked: 0, 1, ... veya direkt JSON
                try:
                    if value.startswith("base64-"):
                        decoded = base64.b64decode(value[7:] + "==").decode("utf-8", errors="ignore")
                    else:
                        decoded = value
                    # JSON parse dene
                    parsed = json.loads(decoded)
                    if isinstance(parsed, list):
                        # chunked: [chunk1, chunk2, ...]
                        decoded = "".join(str(c) for c in parsed)
                        # Tekrar JSON parse
                        try:
                            parsed = json.loads(decoded)
                        except:
                            pass
                    if isinstance(parsed, dict):
                        if "access_token" in parsed:
                            token = parsed["access_token"]
                            break
                        if "currentSession" in parsed and "access_token" in parsed["currentSession"]:
                            token = parsed["currentSession"]["access_token"]
                            break
                except Exception:
                    # Bazen direkt JWT token olarak da olabilir
                    if value.count(".") == 2:
                        token = value
                        break
                    continue
    
    if not token:
        raise HTTPException(401, "Token gerekli (Authorization header veya Supabase cookie)")
    
    sb = get_supabase()
    try:
        result = sb.auth.get_user(token)
        if not result or not result.user:
            raise HTTPException(401, "Token gecersiz")
        u = result.user
        return {
            "id": u.id,
            "email": u.email,
            "role": (u.app_metadata or {}).get("role", "user"),
            "email_confirmed": bool(u.email_confirmed_at),
        }
    except Exception as e:
        raise HTTPException(401, f"Token dogrulanamadi: {e}")


@router.post("/users/set-role-by-email")
def set_user_role_by_email(req: dict):
    """Email ile user bul, role guncelle. Super-admin debug endpoint.
    
    Body: { "email": "...", "role": "admin" | "user" }
    """
    email = req.get("email", "")
    role = req.get("role", "")
    
    if not email or role not in ("admin", "user"):
        raise HTTPException(400, "email ve role ('admin'|'user') gerekli")
    
    sb = get_supabase_admin()
    try:
        # Email ile user bul
        result = sb.auth.admin.list_users(page=1, per_page=200)
        target = None
        for u in result:
            if u.email and u.email.lower() == email.lower():
                target = u
                break
        if not target:
            raise HTTPException(404, f"User bulunamadi: {email}")
        
        current_meta = dict(target.app_metadata or {})
        current_meta["role"] = role
        
        update_result = sb.auth.admin.update_user_by_id(
            target.id,
            {"app_metadata": current_meta}
        )
        return {
            "id": update_result.user.id,
            "email": update_result.user.email,
            "role": role,
            "updated": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Set role failed: {e}")

# ═══════════════════════════════════════════════════════════════
# ─── Audit sıfırlama ────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.post("/reset-audit")
def reset_audit_status():
    """Tüm soruların audit_status = 'pending' yap.
    
    Dikkat: Production'da tüm denetim state sıfırlanır.
    Super admin onayı gerekli (UI confirm).
    """
    sb = get_supabase_admin()
    try:
        result = sb.table("questions").update({
            "audit_status": "pending",
            "is_audited": False,
            "audited_at": None,
        }).neq("id", 0).execute()
        updated = len(result.data) if result.data else 0
        return {"updated": updated, "message": f"{updated} soru audit pending yapildi"}
    except Exception as e:
        raise HTTPException(500, f"Reset failed: {e}")

# ═══════════════════════════════════════════════════════════════
# ─── Password management (super admin only) ─────────────────
# ═══════════════════════════════════════════════════════════════

@router.post("/users/set-password-by-email")
def set_user_password_by_email(req: dict):
    """Email ile user bul, sifresini sifirla (service_role ile).
    
    Body: { "email": "...", "password": "yeni-sifre" }
    
    Super admin onayi gerekir.
    """
    email = req.get("email", "")
    password = req.get("password", "")
    
    if not email or not password:
        raise HTTPException(400, "email ve password gerekli")
    if len(password) < 8:
        raise HTTPException(400, "Password en az 8 karakter")
    
    sb = get_supabase_admin()
    try:
        result = sb.auth.admin.list_users(page=1, per_page=200)
        target = None
        for u in result:
            if u.email and u.email.lower() == email.lower():
                target = u
                break
        if not target:
            raise HTTPException(404, f"User bulunamadi: {email}")
        
        sb.auth.admin.update_user_by_id(
            target.id,
            {"password": password}
        )
        return {
            "id": target.id,
            "email": target.email,
            "password_updated": True,
            "message": f"{email} sifresi guncellendi",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Set password failed: {e}")
