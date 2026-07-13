"""
routers/admin_auth.py
Admin auth router (minimal — sadece temel dependency'ler).

Bağımlılıklar (zaten requirements.txt'te):
  - pyjwt (session JWT)
  - supabase (kullanıcı doğrulama)

Endpoints (prefix /api/v2/admin/auth):
  POST /login        → email + password → session cookie
  POST /logout       → session revoke
  GET  /me           → session validate (frontend guard)

MFA (TOTP) gelecekte eklenecek — ayrı modül gerekli, base install
yeterli değil. Şimdilik password-only auth.
"""

import os
import secrets
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import jwt
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from supabase_client import get_supabase, get_supabase_admin

log = logging.getLogger("pymulakat.admin_auth")

router = APIRouter(prefix="/api/v2/admin/auth", tags=["admin-auth"])

# ═══════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════

ADMIN_JWT_SECRET = os.getenv("ADMIN_JWT_SECRET", "pymulakat-admin-jwt-secret-DO-NOT-USE-IN-PRODUCTION-32+chars")
if ADMIN_JWT_SECRET.startswith("pymulakat-admin-jwt-secret-DO-NOT-USE"):
    log.warning("[admin_auth] ADMIN_JWT_SECRET default kullanılıyor. Production'da set edilmeli!")

SESSION_TTL_HOURS = int(os.getenv("ADMIN_SESSION_TTL_HOURS", "8"))
LOCKOUT_THRESHOLD = int(os.getenv("ADMIN_LOCKOUT_THRESHOLD", "5"))
LOCKOUT_DURATION_MIN = int(os.getenv("ADMIN_LOCKOUT_DURATION_MIN", "15"))


# ═══════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "")[:500]


def write_audit(user_id, email, action, ip, ua, success, detail=None):
    """Admin audit log (best-effort)."""
    try:
        get_supabase_admin().table("admin_audit_log").insert({
            "user_id": user_id,
            "user_email": email,
            "action": action,
            "ip": ip,
            "user_agent": ua,
            "success": success,
            "detail": detail or {},
        }).execute()
    except Exception as e:
        log.error(f"[admin_auth] audit log yazılamadı: {e}")


def get_lockout_status(email: str) -> dict:
    sb = get_supabase_admin()
    try:
        result = sb.table("admin_lockout").select("*").eq("user_email", email).maybe_single().execute()
        if not result.data:
            return {"locked": False, "failed": 0}
        row = result.data
        locked_until = row.get("locked_until")
        if locked_until:
            if isinstance(locked_until, str):
                locked_until = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
            if locked_until > datetime.now(timezone.utc):
                return {"locked": True, "failed": row.get("failed_count", 0)}
        return {"locked": False, "failed": row.get("failed_count", 0)}
    except Exception:
        return {"locked": False, "failed": 0}


def record_failed_login(email: str):
    sb = get_supabase_admin()
    try:
        result = sb.table("admin_lockout").select("*").eq("user_email", email).maybe_single().execute()
        if result.data:
            failed = result.data["failed_count"] + 1
            update = {
                "failed_count": failed,
                "last_attempt_at": datetime.now(timezone.utc).isoformat(),
            }
            if failed >= LOCKOUT_THRESHOLD:
                update["locked_until"] = (
                    datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MIN)
                ).isoformat()
            sb.table("admin_lockout").update(update).eq("user_email", email).execute()
        else:
            sb.table("admin_lockout").insert({
                "user_email": email,
                "failed_count": 1,
                "last_attempt_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
    except Exception as e:
        log.error(f"[admin_auth] record_failed_login hatası: {e}")


def clear_lockout(email: str):
    try:
        get_supabase_admin().table("admin_lockout").delete().eq("user_email", email).execute()
    except Exception:
        pass


def issue_session_token(user_id: str, email: str, ip: str) -> str:
    jti = str(uuid.uuid4())  # admin_sessions.id UUID tipinde (Postgres)
    payload = {
        "sub": user_id,
        "email": email,
        "jti": jti,
        "ip": ip,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS),
    }
    return jwt.encode(payload, ADMIN_JWT_SECRET, algorithm="HS256")


def get_session_from_request(request: Request) -> Optional[dict]:
    # 1) Authorization header
    auth = request.headers.get("authorization", "")
    token = ""
    if auth.startswith("Bearer "):
        token = auth[7:]

    # 2) Cookie
    if not token:
        token = request.cookies.get("admin_session", "")

    if not token:
        return None

    try:
        payload = jwt.decode(token, ADMIN_JWT_SECRET, algorithms=["HS256"])
        # jti DB'de var mı + revoked mi?
        sb = get_supabase_admin()
        # jti UUID string — Supabase PostgREST otomatik cast eder
        result = sb.table("admin_sessions").select("*").eq("id", payload["jti"]).maybe_single().execute()
        if not result.data or result.data.get("revoked"):
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════

@router.post("/login")
def login(req: LoginRequest, request: Request, response: Response):
    """Email + password → session cookie.
    
    Akış:
    1. Lockout kontrol
    2. Supabase signIn (password validate)
    3. Admin role kontrol
    4. Session JWT issue + cookie set
    """
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    email = req.email.lower().strip()

    # 1) Lockout
    lockout = get_lockout_status(email)
    if lockout["locked"]:
        write_audit(None, email, "login", ip, ua, False, {"reason": "locked"})
        raise HTTPException(
            status_code=429,
            detail="Hesap kilitli. 15dk sonra tekrar deneyin.",
        )

    # 2) Supabase signIn
    sb = get_supabase()
    try:
        result = sb.auth.sign_in_with_password({"email": email, "password": req.password})
    except Exception as e:
        log.error(f"[admin_auth] signIn exception: {type(e).__name__}: {e}")
        record_failed_login(email)
        write_audit(None, email, "login", ip, ua, False, {"reason": "auth_failed", "error": str(e)[:200]})
        raise HTTPException(status_code=401, detail="Geçersiz email veya şifre")

    if not result or not result.user:
        record_failed_login(email)
        write_audit(None, email, "login", ip, ua, False, {"reason": "no_user"})
        raise HTTPException(status_code=401, detail="Geçersiz email veya şifre")

    user = result.user
    user_id = user.id

    # 3) Admin role kontrol
    app_role = (user.app_metadata or {}).get("role", "user")
    if app_role != "admin":
        record_failed_login(email)
        write_audit(user_id, email, "login", ip, ua, False, {"reason": "not_admin"})
        raise HTTPException(status_code=401, detail="Geçersiz email veya şifre")

    # 4) Session
    session_jwt = issue_session_token(user_id, email, ip)
    jti = jwt.decode(session_jwt, options={"verify_signature": False})["jti"]
    try:
        get_supabase_admin().table("admin_sessions").insert({
            "id": jti,
            "user_id": user_id,
            "ip": ip,
            "user_agent": ua,
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)).isoformat(),
        }).execute()
    except Exception as e:
        log.error(f"[admin_auth] admin_sessions insert failed: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Session yazma hatası: {str(e)[:200]}")
    clear_lockout(email)
    try:
        write_audit(user_id, email, "login", ip, ua, True, {"stage": "complete"})
    except Exception as e:
        log.error(f"[admin_auth] audit log failed: {e}")

    # Set-Cookie: JSONResponse headers dict ile güvenilir şekilde set edilir
    # (response.set_cookie() Starlette'ta bazen düşmüyor)
    cookie_parts = [
        f"admin_session={session_jwt}",
        f"Max-Age={SESSION_TTL_HOURS * 3600}",
        "Path=/",
        "HttpOnly",
        "Secure",
        "SameSite=Strict",
    ]
    set_cookie_header = "; ".join(cookie_parts)

    return JSONResponse(
        {
            "authenticated": True,
            "user": {"id": user_id, "email": email, "role": "admin"},
        },
        headers={"Set-Cookie": set_cookie_header},
    )


@router.post("/logout")
def logout(request: Request, response: Response):
    payload = get_session_from_request(request)
    if payload:
        try:
            get_supabase_admin().table("admin_sessions").update({
                "revoked": True,
                "revoked_at": datetime.now(timezone.utc).isoformat(),
                "revoke_reason": "logout",
            }).eq("id", payload["jti"]).execute()
            write_audit(payload["sub"], payload.get("email"), "logout", get_client_ip(request), get_user_agent(request), True, {})
        except Exception:
            pass
    # Delete cookie — manuel header
    delete_cookie_header = "admin_session=; Path=/; Domain=pythonmulakat.com; Max-Age=0; HttpOnly; Secure; SameSite=Lax"
    return JSONResponse({"ok": True}, headers={"Set-Cookie": delete_cookie_header})


@router.get("/me")
def me(request: Request):
    payload = get_session_from_request(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Session yok veya süresi dolmuş")
    # IP binding KAPALI: Vercel serverless fetch yaparken egress IP degisiyor
    # (login IP != /me IP, redirect loop olusuyor)
    # Production'da farkli IP'lerden ayni cookie ile giris kabul edilir
    # (güvenlik: HttpOnly + Secure + SameSite=Strict cookie yeterli)
    return {
        "id": payload["sub"],
        "email": payload.get("email"),
        "role": "admin",
        "expires_at": datetime.fromtimestamp(payload["exp"], tz=timezone.utc).isoformat(),
    }
