import logging
import time
import json
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import importlib

# ─── Logging config (JSON line output for Vercel log aggregation) ──
class JsonFormatter(logging.Formatter):
    """JSON line output — Vercel log streaming ile uyumlu."""
    def format(self, record):
        payload = {
            "ts": int(record.created * 1000),
            "level": record.levelname,
            "name": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

_handler = logging.StreamHandler(sys.stderr)
if os.getenv("LOG_FORMAT", "json") == "plain":
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
else:
    _handler.setFormatter(JsonFormatter())

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "WARNING").upper(),
    handlers=[_handler],
    force=True,
)

logger = logging.getLogger("pymulakat")

# ─── Python path ────────────────────────────────────────
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("=" * 60)
print("🚀 PythonMulakat API başlatılıyor (v2.5)...")
print("=" * 60)

# 🆕 SEO içeriklerini QUESTIONS'e uygula (explanation, complexity, related_concepts, ...)
try:
    from data.SEO_CONTENT import apply_seo_content
    apply_seo_content()
except Exception as e:
    print(f"⚠️ SEO content yüklenemedi: {e}")

# ─── App oluştur ────────────────────────────────────────
app = FastAPI(title="PythonMulakat API", version="2.4")

@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    """Request süresi + slow request warning (response header X-Response-Time-ms)."""
    t0 = time.time()
    response: Response = await call_next(request)
    dur_ms = int((time.time() - t0) * 1000)
    response.headers["X-Response-Time-ms"] = str(dur_ms)
    if dur_ms > 2000:
        logger.warning(f"slow request {request.url.path} {dur_ms}ms")
    return response


# ─── CORS — env-driven explicit allow-list (wildcard yok) ────────────
_default_origins = ",".join([
    "https://www.pythonmulakat.com",
    "https://pythonmulakat.com",
    "https://pymulakat-frontend.vercel.app",
    "https://pymulakat-backend.vercel.app",
    "http://localhost:3000",
])
_ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()
]
_VERCEL_REGEX = os.getenv("ALLOW_VERCEL_PREVIEW", "1") == "1"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app" if _VERCEL_REGEX else None,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # limited methods
    allow_headers=["*"],
    max_age=600,  # 10 min cache for OPTIONS preflight
)
logger.info(f"CORS allowed origins: {_ALLOWED_ORIGINS}")


# ─── Router'ları güvenli yükle + include et ──────────────
def try_include(name: str, label: str):
    """Modülü import et ve router'ı app'e include et."""
    try:
        mod = importlib.import_module(name)
        if not hasattr(mod, "router"):
            print(f"⚠️ {label}: router attribute YOK")
            return None

        app.include_router(mod.router)
        prefix = getattr(mod.router, "prefix", "?")
        print(f"✅ {label}: {prefix}")
        return mod
    except Exception as e:
        print(f"❌ {label} yüklenemedi: {e}")
        return None


# ─── v1 (eski) ──────────────────────────────────────────
auth_module = try_include("routers.auth", "auth")
attempts_v1 = try_include("routers.attempts", "attempts (v1)")

# ─── v2 (yeni) ──────────────────────────────────────────
questions_v2 = try_include("routers.questions", "questions (v2)")

categories_v2 = try_include("routers.categories", "categories (v2)")
tutorials_v2 = try_include("routers.tutorials", "tutorials (v2)")
account_v2 = try_include("routers.account", "account (KVKK delete)")
forms_v2 = try_include("routers.forms", "forms (user posts)")
recommendations_v2 = try_include("routers.recommendations", "recommendations (deterministic)")
play_count_v2 = try_include("routers.play_count", "play count (user activity)")
guides_v1 = try_include("routers.guides", "guides (study materials)")

# ═══════════════════════════════════════════════════════════════
# Admin v2: 4 eski router'ı (admin, admin_auth, audit, analytics)
# TEK router'da toplar. main.py'de tek include yeterli.
# URL prefix'leri korundu → frontend değişmedi.
# ═══════════════════════════════════════════════════════════════
# Admin v2: 4 eski router tek dosyada (admin_v2.py)
# Admin v2: 4 sub-router route'larini manuel app.routes'a ekle
# (app.include_router sub-routes flatten etmiyor, FastAPI quirk)
admin_v2_module = None
try:
    from routers.admin_v2 import sub_routers as _admin_v2_subs
    from routers.admin_setup import router as _setup_sub
    from routers.admin_profile import router as _profile_sub
    _admin_v2_subs.append(("setup", _setup_sub))
    _admin_v2_subs.append(("profile", _profile_sub))
    added = 0
    for _name, _r in _admin_v2_subs:
        # Sub router'daki her route'u app.routes'a ekle
        for _route in _r.routes:
            # APIRoute objesi ise ekle
            if hasattr(_route, "path") and hasattr(_route, "endpoint"):
                # Prefix'i ekle
                if not hasattr(_route, "_admin_v2_added"):
                    # app.include_router kullan AMA route zaten prefix'li (sub-router prefix ile)
                    try:
                        app.include_router(_r)  # idempotent
                    except Exception:
                        pass
                    added += 1
    # Yine app.include_router ile dene (duplicate safe)
    for _name, _r in _admin_v2_subs:
        try:
            app.include_router(_r)
        except Exception:
            pass
    print(f"✅ admin v2 facade: {len(_admin_v2_subs)} sub-router (manuel flatten)")
    admin_v2_module = True
except Exception as e:
    print(f"❌ admin v2 facade hatasi: {e}")
# audit endpoints: routers/admin.py üzerinden yüklenir (router prefix çakışması önlemek için)
# 📌 Mail koçu endpointleri kaldirildi (KVKK uyumu).
# Sadece database tablolarinda varsa email gerekiyor, mail gonderimi YOK.


@app.get("/health")
def health():
    """Production-grade health check: DB connectivity + module status.

    200 = everything OK
    503 = DB unreachable (load balancer should mark unhealthy)
    """
    from fastapi.responses import JSONResponse

    loaded = {
        "auth": auth_module is not None,
        "attempts_v1": attempts_v1 is not None,
        "questions_v2": questions_v2 is not None,
        "categories_v2": categories_v2 is not None,
        "tutorials_v2": tutorials_v2 is not None,
        "admin": admin_v2_module is not None,
        "account_v2": account_v2 is not None,
    }

    # DB connectivity check
    db_ok = False
    db_error = None
    try:
        from supabase_client import get_supabase
        sb = get_supabase()
        # Lightweight query
        sb.table("questions").select("id").limit(1).execute()
        db_ok = True
    except Exception as e:
        db_error = str(e)[:200]

    payload = {
        "status": "ok" if db_ok else "degraded",
        "version": "2.5",
        "loaded": loaded,
        "db": {
            "ok": db_ok,
            "error": db_error,
        },
        "total_routes": len(app.routes),
    }

    status_code = 200 if db_ok else 503
    if not db_ok:
        logger.warning(f"health check degraded: db_error={db_error}")

    return JSONResponse(payload, status_code=status_code)


@app.get("/")
def root():
    return {
        "service": "PythonMulakat API",
        "version": "2.5",
        "endpoints": {
            "register": "POST /auth/register",
            "verify_email": "POST /auth/verify-email",
            "login": "POST /auth/login",
            "me": "GET /auth/me",
            "categories": "GET /api/v2/categories",
            "all_questions": "GET /api/v2/questions/all",
            "questions": "GET /api/v2/questions?category=python-basics",
            "question_detail": "GET /api/v2/questions/1",
            "tests": "GET /api/v2/questions/1/tests (auth)",
            "progress": "GET /api/v2/questions/1/progress (auth)",
            "submit_attempt": "POST /api/v2/attempts (auth)",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)

# Trigger redeploy Wed Jul  1 04:44:33 UTC 2026
# Wed Jul  1 04:49:15 UTC 2026
# Admin status check 1782881637
