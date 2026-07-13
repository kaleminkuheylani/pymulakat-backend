"""
routers/user_check.py
User kimlik dogrulama + is_admin kontrol endpoint'i.

Browser'dan Supabase auth cookie ile user_id alinir,
profiles tablosundan is_admin sorgulanir.

Endpointler (prefix /api/v2/user):
  GET /me     → user_id + email + is_admin (auth cookie ile)
"""

import logging
from fastapi import APIRouter, HTTPException, Request
from supabase_client import get_supabase, get_supabase_admin

log = logging.getLogger("pymulakat.user_check")

router = APIRouter(prefix="/api/v2/user", tags=["user-check"])


def extract_user_id_from_cookies(request: Request) -> str | None:
    """Supabase auth cookie'lerinden user_id cikar.

    Supabase'in auth storage formati:
    sb-<project>-auth-token = base64url(JSON) chunked
    veya localStorage sb-<project>-auth-token

    Browser'da credential cookie gonderilir:
    sb-pymulakat-auth-token (eger set edilmisse)
    veya chunked (sb-pymulakat-auth-token-chunk-0, ...)
    """
    cookies = request.cookies
    # Once chunked'lari birlestir
    chunk_count = 0
    chunks = []
    for key in cookies.keys():
        if key.startswith("sb-pymulakat-auth-token-chunk-"):
            chunk_count += 1
            chunks.append((key, cookies[key]))

    if chunk_count > 0:
        # Siraya gore birlestir
        chunks.sort(key=lambda x: int(x[0].split("-")[-1]))
        combined = "".join(v for _, v in chunks)
        # base64url decode
        import base64
        import json
        try:
            # URL-safe base64 padding
            padded = combined + "=" * (-len(combined) % 4)
            # URL-safe characters replace
            padded = padded.replace("-", "+").replace("_", "/")
            decoded = base64.b64decode(padded).decode("utf-8")
            data = json.loads(decoded)
            return data.get("user", {}).get("id")
        except Exception as e:
            log.debug(f"[user_check] chunked decode hatasi: {e}")

    # Tek cookie (base64)
    raw = cookies.get("sb-pymulakat-auth-token", "")
    if raw:
        import base64
        import json
        try:
            padded = raw + "=" * (-len(raw) % 4)
            padded = padded.replace("-", "+").replace("_", "/")
            decoded = base64.b64decode(padded).decode("utf-8")
            data = json.loads(decoded)
            return data.get("user", {}).get("id")
        except Exception as e:
            log.debug(f"[user_check] single cookie decode hatasi: {e}")

    return None


@router.get("/me")
def me(request: Request):
    """User kimlik + is_admin dondurur. Supabase auth cookie ile.

    Response:
      { id, email, username, is_admin, is_verified }

    Cookie yoksa 401.
    """
    user_id = extract_user_id_from_cookies(request)
    if not user_id:
        # Alternatif: Authorization header (Bearer access_token)
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            try:
                # Supabase user bilgisi getir
                sb = get_supabase()
                user_resp = sb.auth.get_user(token)
                if user_resp and user_resp.user:
                    user_id = user_resp.user.id
            except Exception as e:
                log.debug(f"[user_check] Bearer token hatasi: {e}")

    if not user_id:
        raise HTTPException(401, "Auth cookie/token gerekli")

    sb = get_supabase_admin()
    try:
        result = sb.table("profiles").select(
            "id, email, username, is_admin, is_verified"
        ).eq("id", user_id).maybe_single().execute()
    except Exception as e:
        log.error(f"[user_check] profile sorgu hatasi: {e}")
        raise HTTPException(500, f"Profile sorgulanamadi: {str(e)[:200]}")

    if not result.data:
        # Profile henuz olusturulmamis (yeni signup)
        return {
            "id": user_id,
            "email": None,
            "username": None,
            "is_admin": False,
            "is_verified": False,
            "profile_missing": True,
        }

    profile = result.data
    return {
        "id": profile.get("id"),
        "email": profile.get("email"),
        "username": profile.get("username"),
        "is_admin": bool(profile.get("is_admin", False)),
        "is_verified": bool(profile.get("is_verified", False)),
        "profile_missing": False,
    }
