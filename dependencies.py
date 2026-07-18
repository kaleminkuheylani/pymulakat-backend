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
    """Bearer <jwt> + sb-*-auth-token cookie → Supabase ile doğrula.

    2026-07-14: Cookie fallback eklendi. Supabase SSR httpOnly cookie
    kullaniyor (sb-{project_ref}-auth-token), JS erisemez, sadece
    server'a gider. Authorization header yoksa cookie'den user al.
    """
    # Header'ı manuel olarak al
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")

    # 1) Authorization: Bearer <jwt> (varsa)
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "").strip()

    # 2) Cookie fallback — sb-*-auth-token (httpOnly, supabase-ssr)
    # JSON encoded: { access_token, refresh_token, expires_at, ... }
    if not token:
        try:
            import json as _json
            for cookie_name, cookie_value in request.cookies.items():
                if cookie_name.startswith("sb-") and cookie_name.endswith("-auth-token"):
                    try:
                        parsed = _json.loads(cookie_value)
                        if isinstance(parsed, list):
                            for chunk in parsed:
                                if isinstance(chunk, dict) and chunk.get("access_token"):
                                    token = chunk["access_token"]
                                    break
                        elif isinstance(parsed, dict) and parsed.get("access_token"):
                            token = parsed["access_token"]
                        if token:
                            break
                    except Exception:
                        if cookie_value.startswith("eyJ"):
                            token = cookie_value
                            break
        except Exception:
            pass

    if not token:
        raise HTTPException(401, "Geçersiz token formatı.")

    # JWT decode yöntemi (Supabase v2'de get_user() çalışmıyor)
    jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")
    app_env = os.environ.get("APP_ENV", "development").lower()

    if jwt_secret:
        # Secret varsa tam doğrulama yap (HS256, legacy)
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
        except (jwt.InvalidTokenError, Exception):
            # HS256 başarısız (ES256 olabilir veya signature farklı),
            # Supabase client fallback dene (JWKS otomatik)
            pass

    # HS256 başarısız veya secret yok — Supabase client fallback (ES256/JWKS)
    # 2026-07-18: Google/GitHub OAuth token RS256 (Supabase public key ile imzali),
    # service_role key ile get_user(jwt=token) Supabase Auth API'sini cagirir.
    # Supabase v2 SDK yeni yontem: supabase.auth.get_user(jwt=token)
    try:
        from supabase_client import get_supabase
        sb = get_supabase()  # anon key, public key JWKS otomatik ceker
        user_response = sb.auth.get_user(jwt=token)
        if user_response and user_response.user:
            return {
                "id": str(user_response.user.id),
                "email": user_response.user.email,
            }
    except Exception as e1:
        # Service role fallback (RLS bypass, user kontrolu icin)
        try:
            from supabase_client import get_supabase_admin
            sb_admin = get_supabase_admin()
            user_response = sb_admin.auth.get_user(jwt=token)
            if user_response and user_response.user:
                return {
                    "id": str(user_response.user.id),
                    "email": user_response.user.email,
                }
        except Exception as e2:
            logger.warning("get_user_failed anon=%s admin=%s", str(e1)[:80], str(e2)[:80])

    # HS256 + ES256 ikisi de başarısız → 401
    raise HTTPException(401, "Token doğrulanamadı (HS256 + ES256 başarısız).")

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