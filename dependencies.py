import logging
import os

import jwt
from fastapi import HTTPException, Request

from supabase_client import get_supabase

logger = logging.getLogger("pymulakat")


# ═══════════════════════════════════════════════════════════════
# Request helpers (TEK KAYNAK — duplicate temizligi 2026-07-13)
# Onceki: get_client_ip + get_user_agent 3 dosyada kopyalanmisti
#   (admin_auth.py, admin_profile.py, analytics.py)
# Simdi: TEK tanim, 3 dosya import eder.
# ═══════════════════════════════════════════════════════════════

def get_client_ip(request: Request, fallback: str = "unknown") -> str:
    """x-forwarded-for header'indan ilk IP, yoksa request.client.host.

    Args:
        request: FastAPI Request
        fallback: client.host da yoksa donulecek deger (default "unknown").
                  analytics.py "0.0.0.0" bekliyor, override eder.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else fallback


def get_user_agent(request: Request, max_length: int = 500) -> str:
    """user-agent header'i, max_length ile truncate."""
    return request.headers.get("user-agent", "")[:max_length]


async def get_current_user(request: Request):
    """Bearer <jwt> → Supabase ile doğrula.

    Header(...) yerine Request kullan — daha güvenilir.
    """
    # Header'ı manuel olarak al
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Geçersiz token formatı.")

    token = auth_header.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(401, "Token boş olamaz.")

    # JWT decode yöntemi (Supabase v2'de get_user() çalışmıyor)
    jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")
    app_env = os.environ.get("APP_ENV", "development").lower()

    if jwt_secret:
        # Secret varsa tam doğrulama yap
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
            user_id = payload.get("sub")
            email = payload.get("email")

            if not user_id:
                raise HTTPException(401, "Token'da user bilgisi yok.")

            return {"id": str(user_id), "email": email}
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token süresi dolmuş.")
        except jwt.InvalidTokenError as e:
            raise HTTPException(401, f"Geçersiz token: {e}")

    # Secret yoksa — fail fast in production, warn in dev
    if app_env == "production":
        # Production'da secret zorunlu — startup'ta patlamalı
        raise RuntimeError(
            "SUPABASE_JWT_SECRET zorunlu! APP_ENV=production ama secret tanımsız. "
            "Supabase Dashboard → Settings → API → JWT Secret"
        )

    # Geliştirme modunda: uyar + verify'siz decode
    logger.warning(
        "⚠️ SUPABASE_JWT_SECRET tanımsız — geliştirme modunda verify'siz decode aktif. "
        "Production'da MUTLAKA ayarlayın!"
    )
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise HTTPException(401, "Token'da user bilgisi yok.")

        return {"id": str(user_id), "email": email}
    except Exception as e:
        raise HTTPException(401, f"Token decode edilemedi: {e}")