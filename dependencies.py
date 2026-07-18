import logging
import os
import urllib.request
import json as _json

import jwt
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
# Supabase token dogrulama — minimal, 3 yol:
#   1) Authorization header
#   2) sb-*-auth-token cookie
#   3) Token yoksa 401
#
# Dogrulama: HS256 (SUPABASE_JWT_SECRET varsa) veya
#            Supabase Auth API /auth/v1/user (raw HTTP)
# ═══════════════════════════════════════════════════════════════

async def get_current_user(request: Request):
    # 1) Authorization header
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "").strip()

    # 2) Cookie fallback
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
                    if cookie_value.startswith("eyJ"):
                        token = cookie_value
                if token:
                    break

    if not token:
        raise HTTPException(401, "Geçersiz token formatı.")

    # Dogrulama — once HS256
    jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")
    if jwt_secret:
        try:
            payload = jwt.decode(
                token, jwt_secret, algorithms=["HS256"], audience="authenticated"
            )
            user_id = payload.get("sub")
            email = payload.get("email")
            if user_id:
                return {"id": str(user_id), "email": email}
        except Exception:
            pass  # HS256 basarisiz, fallback dene

    # Fallback — Supabase Auth API raw HTTP
    supabase_url = os.environ.get("SUPABASE_URL")
    if supabase_url:
        try:
            req = urllib.request.Request(
                f"{supabase_url.rstrip('/')}/auth/v1/user",
                headers={"Authorization": f"Bearer {token}", "apikey": os.environ.get("SUPABASE_ANON_KEY", "")},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = _json.loads(resp.read())
                if data and data.get("id"):
                    return {"id": str(data["id"]), "email": data.get("email")}
        except Exception as e:
            logger.warning("supabase_auth_api_failed: %s", str(e)[:120])

    raise HTTPException(401, "Token doğrulanamadı.")
