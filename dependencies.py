import logging
import os
import urllib.request
import json as _json
from functools import lru_cache
from threading import Lock

import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, Request

logger = logging.getLogger("pymulakat")


# ═══════════════════════════════════════════════════════════════
# Request helpers — TEK KAYNAK
# ═══════════════════════════════════════════════════════════════

def get_client_ip(request: Request, fallback: str = "unknown") -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else fallback


def get_user_agent(request: Request, max_length: int = 500) -> str:
    return request.headers.get("user-agent", "")[:max_length]


# ═══════════════════════════════════════════════════════════════
# Supabase JWKS — TEK KAYNAK
#
# 2026-07-19: Supabase yeni projeleri (>= 2024) ES256 (P-256) kullanir,
# HS256/RS256 DEGIL. Public key Supabase JWKS endpoint'inden cekilir:
#   https://<project>.supabase.co/auth/v1/.well-known/jwks.json
#
# PyJWKClient JWKS'i otomatik cache'ler (1 saat). Her istekte yeniden
# cekmez, performansli.
# ═══════════════════════════════════════════════════════════════

_jwks_client: PyJWKClient | None = None
_jwks_lock = Lock()


def _get_jwks_client() -> PyJWKClient | None:
    """Singleton JWKS client. Supabase URL degistiyse resetlenir."""
    global _jwks_client
    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    if not supabase_url:
        return None
    jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"

    with _jwks_lock:
        if _jwks_client is None:
            try:
                _jwks_client = PyJWKClient(
                    jwks_url,
                    cache_jwk_set=True,
                    lifespan=3600,
                    timeout=5,
                )
                logger.info("supabase_jwks_client_init: %s", jwks_url)
            except Exception as e:
                logger.warning("jwks_client_init_failed: %s", str(e)[:200])
                return None
        return _jwks_client


def reset_jwks_client() -> None:
    """Test/admin: client'i resetle (env degisikligi vb.)."""
    global _jwks_client
    with _jwks_lock:
        _jwks_client = None


# ═══════════════════════════════════════════════════════════════
# Supabase token dogrulama — 3 katman:
#   A) ES256 + JWKS (Supabase yeni projeler — varsayilan)
#   B) HS256 + SUPABASE_JWT_SECRET (eski Supabase projeleri, fallback)
#   C) Supabase /auth/v1/user (GoTrue, son care)
#
# Bearer header veya sb-*-auth-token cookie'den token al.
# ═══════════════════════════════════════════════════════════════

async def get_current_user(request: Request):
    # ── Token'i 3 kanaldan oku ──
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "").strip()

    if not token:
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
                except Exception:
                    # Duz JWT string cookie (nadir)
                    if cookie_value.startswith("eyJ"):
                        token = cookie_value
                if token:
                    break

    if not token:
        raise HTTPException(401, "Geçersiz token formatı.")

    # ── ADIM A: ES256 + JWKS (yeni Supabase varsayilani) ──
    jwks_client = _get_jwks_client()
    if jwks_client:
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256", "HS256"],  # Supabase'in verebilecegi hepsi
                audience="authenticated",
            )
            user_id = payload.get("sub")
            email = payload.get("email")
            if user_id:
                return {"id": str(user_id), "email": email}
        except jwt.ExpiredSignatureError:
            logger.info("jwt_expired_es256")
            raise HTTPException(401, "Token süresi dolmuş.")
        except Exception as e:
            err_msg = str(e)[:200]
            # ES256 basarisiz olabilir (eski proje HS256 kullanir)
            logger.info("es256_decode_failed_fallback_to_hs256: %s", err_msg)

    # ── ADIM B: HS256 + SUPABASE_JWT_SECRET (eski Supabase) ──
    jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")
    if jwt_secret:
        try:
            payload = jwt.decode(
                token, jwt_secret, algorithms=["HS256"], audience="authenticated"
            )
            user_id = payload.get("sub")
            email = payload.get("email")
            if user_id:
                logger.info("hs256_decode_ok (legacy Supabase project)")
                return {"id": str(user_id), "email": email}
        except Exception as e:
            logger.info("hs256_decode_failed: %s", str(e)[:120])

    # ── ADIM C: Supabase Auth API raw HTTP (son care) ──
    supabase_url = os.environ.get("SUPABASE_URL")
    if supabase_url:
        try:
            # Hem anon hem service_role key dene (service_role daha guvenilir)
            api_key = (
                os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
                or os.environ.get("SUPABASE_ANON_KEY")
                or ""
            )
            req = urllib.request.Request(
                f"{supabase_url.rstrip('/')}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": api_key,
                },
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = _json.loads(resp.read())
                if data and data.get("id"):
                    return {"id": str(data["id"]), "email": data.get("email")}
        except Exception as e:
            err_msg = str(e)[:200]
            logger.warning("supabase_auth_api_failed: %s", err_msg)

    raise HTTPException(401, "Token doğrulanamadı.")
