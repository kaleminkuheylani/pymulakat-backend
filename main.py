from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import importlib

# ─── Python path ────────────────────────────────────────
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("=" * 60)
print("🚀 PythonMulakat API başlatılıyor (v2.4)...")
print("=" * 60)

# 🆕 SEO içeriklerini QUESTIONS'e uygula (explanation, complexity, related_concepts, ...)
try:
    from data.SEO_CONTENT import apply_seo_content
    apply_seo_content()
except Exception as e:
    print(f"⚠️ SEO content yüklenemedi: {e}")

# ─── App oluştur ────────────────────────────────────────
app = FastAPI(title="PythonMulakat API", version="2.4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.pythonmulakat.com",
        "https://pythonmulakat.com",
        "https://pymulakat.vercel.app",
        "https://pymulakat-frontend.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
interviews_v1 = try_include("routers.interviews", "interviews (v1)")
attempts_v1 = try_include("routers.attempts", "attempts (v1)")

# ─── v2 (yeni) ──────────────────────────────────────────
questions_v2 = try_include("routers.questions", "questions (v2)")
debug_module = try_include("routers.debug", "debug")

categories_v2 = try_include("routers.categories", "categories (v2)")
tutorials_v2 = try_include("routers.tutorials", "tutorials (v2)")
admin_module = try_include("routers.admin", "admin (migration)")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "2.4",
        "loaded": {
            "auth": auth_module is not None,
            "interviews_v1": interviews_v1 is not None,
            "attempts_v1": attempts_v1 is not None,
            "questions_v2": questions_v2 is not None,
            "categories_v2": categories_v2 is not None,
            "tutorials_v2": tutorials_v2 is not None,
            "debug": debug_module is not None,
            "admin": admin_module is not None,
        },
        "total_routes": len(app.routes),
    }


@app.get("/")
def root():
    return {
        "service": "PythonMulakat API",
        "version": "2.4",
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
