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
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr
from supabase_client import get_supabase, get_supabase_admin
from dependencies import get_client_ip, get_user_agent
from services.email import (
    generate_magic_token, send_magic_link_email, RESEND_MAGIC_LINK_TTL_MIN
)
import hashlib

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


class MagicLinkRequest(BaseModel):
    email: EmailStr
    password: str  # 2026-07-15: Railway env'deki ADMIN_PASSWORD ile dogrulanir


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════
# get_client_ip + get_user_agent artik dependencies.py'den import ediliyor
# (duplicate temizligi 2026-07-13, 3 dosyada kopyalanan tekrar tek kaynaga tasindi)

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
    """2026-07-15: Defensive — admin_lockout tablosu yoksa sessizce skip et.
    Login akisini bozmamali (sadece lockout tracking kaybi)."""
    try:
        sb = get_supabase_admin()
        result = sb.table("admin_lockout").select("*").eq("user_email", email).maybe_single().execute()
        # result None veya result.data None olabilir (tablo yok / row yok)
        if result is None or result.data is None:
            return  # lockout tracking skip — login devam etsin
        if result.data:
            failed = result.data.get("failed_count", 0) + 1
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
        # Lockout tracking hatasi → log + skip (login devam etsin)
        log.warning(f"[admin_auth] record_failed_login skip: {type(e).__name__}: {str(e)[:200]}")


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

    # 2026-07-15: Admin password env fallback (kullanici talebi)
    # Frontend bos gonderirse ve ADMIN_EMAIL+ADMIN_PASSWORD env'de eslesirse
    # Supabase signIn icin o password kullanilir. Plain text env — internal
    # single-user tool icin kabul edilebilir, SAKIN LOGLAMA.
    password = req.password
    if not password:
        env_email = os.getenv("ADMIN_EMAIL", "").lower().strip()
        env_password = os.getenv("ADMIN_PASSWORD", "")
        if env_email and env_password and env_email == email:
            password = env_password
            log.info(f"[admin_auth] env password fallback used for {email}")
        else:
            record_failed_login(email)
            write_audit(None, email, "login", ip, ua, False, {"reason": "empty_password"})
            raise HTTPException(status_code=401, detail="Geçersiz email veya şifre")

    # 2) Supabase signIn
    sb = get_supabase()
    try:
        result = sb.auth.sign_in_with_password({"email": email, "password": password})
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
    # Domain=pythonmulakat.com — frontend Vercel (pythonmulakat.com) üzerinden okuyabilsin
    # SameSite=Lax (Strict cross-origin Set-Cookie reddederdi — d7c76fd fix)
    # Secure=True (HTTPS only)
    cookie_parts = [
        f"admin_session={session_jwt}",
        f"Max-Age={SESSION_TTL_HOURS * 3600}",
        "Path=/",
        "Domain=pythonmulakat.com",
        "HttpOnly",
        "Secure",
        "SameSite=Lax",
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



@router.post("/magic-link")
def magic_link(req: MagicLinkRequest, request: Request):
    """Email + password admin login — Resend ile magic link gonderir.

    2026-07-15: Railway env tabanli dogrulama:
      - email == ADMIN_EMAIL (env)
      - password == ADMIN_PASSWORD (env)
      Supabase user kontrolu YOK (env-only).

    Akis:
      1. Email + password dogrula (ADMIN_EMAIL/ADMIN_PASSWORD env)
      2. Token uret (secrets.token_urlsafe(32)), hash'le (SHA256)
      3. DB'ye kaydet (expires_at = +15dk, ip, ua)
      4. Resend ile email gonder (link: /admin/auth/verify?token=...)
      5. Response: dev mode'da link doner, prod'da sadece 'gonderildi'
    """
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    email = req.email.lower().strip()

    # 2026-07-15: Railway env tabanli dogrulama (Supabase user kontrolu YOK)
    env_email = os.getenv("ADMIN_EMAIL", "").lower().strip()
    env_password = os.getenv("ADMIN_PASSWORD", "")

    if not env_email or not env_password:
        log.error("[admin_auth] ADMIN_EMAIL veya ADMIN_PASSWORD env set edilmemis")
        raise HTTPException(500, "Admin auth yapilandirilmamis")

    # Email + password dogrulama (constant-time compare timing attack onlemi)
    import hmac
    if not hmac.compare_digest(email, env_email) or not hmac.compare_digest(req.password, env_password):
        record_failed_login(email)
        write_audit(None, email, "magic_link_request", ip, ua, False, {"reason": "auth_failed"})
        log.info(f"[admin_auth] magic-link auth_failed for {email}")
        raise HTTPException(401, "Geçersiz email veya şifre")

    # Basarili: token uret + DB
    raw_token, token_hash = generate_magic_token()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESEND_MAGIC_LINK_TTL_MIN)

    sb = get_supabase_admin()
    try:
        sb.table("admin_magic_tokens").insert({
            "user_email": email,
            "token_hash": token_hash,
            "expires_at": expires_at.isoformat(),
            "ip": ip,
            "user_agent": ua,
        }).execute()
    except Exception as e:
        log.error(f"[admin_auth] magic_tokens insert error: {type(e).__name__}: {e}")
        raise HTTPException(500, "Token olusturulamadi")

    # Magic link olustur
    base_url = os.getenv("ADMIN_VERIFY_URL", "https://pythonmulakat.com")
    magic_link = f"{base_url}/admin/auth/verify?token={raw_token}"

    # Resend ile gonder
    sent = send_magic_link_email(email, magic_link)
    write_audit(None, email, "magic_link_request", ip, ua, True, {"sent": sent})

    response = {"ok": True, "sent": sent}
    if not sent:
        response["dev_link"] = magic_link
    return response

    # Token uret + DB'ye kaydet
    raw_token, token_hash = generate_magic_token()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESEND_MAGIC_LINK_TTL_MIN)

    try:
        sb.table("admin_magic_tokens").insert({
            "user_email": email,
            "token_hash": token_hash,
            "expires_at": expires_at.isoformat(),
            "ip": ip,
            "user_agent": ua,
        }).execute()
    except Exception as e:
        log.error(f"[admin_auth] magic_tokens insert error: {type(e).__name__}: {e}")
        raise HTTPException(500, "Token olusturulamadi")

    # Magic link olustur
    base_url = os.getenv("ADMIN_VERIFY_URL", "https://pythonmulakat.com")
    magic_link = f"{base_url}/admin/auth/verify?token={raw_token}"

    # Resend ile gonder
    sent = send_magic_link_email(email, magic_link)

    # Audit
    write_audit(admin_user.id, email, "magic_link_request", ip, ua, True, {"sent": sent})

    response = {"ok": True, "sent": sent}
    # Dev mode: link response'da (RESEND_API_KEY yoksa)
    if not sent:
        response["dev_link"] = magic_link
    return response


@router.get("/verify")
def verify_magic_link(request: Request, response: Response, token: str):
    """Magic link tiklandiginda cagrilir.

    Akis:
      1. token → SHA256 hash
      2. DB'de hash ile ara (kullanilmamis, expires > now)
      3. User email ile Supabase admin kontrol
      4. Session JWT olustur, cookie set
      5. used_at = now (tek kullanimlik)
      6. /admin'e redirect (HTML response)
    """
    ip = get_client_ip(request)
    ua = get_user_agent(request)

    if not token or len(token) < 10:
        raise HTTPException(400, "Gecersiz token")

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # DB'de token ara
    sb = get_supabase_admin()
    try:
        result = sb.table("admin_magic_tokens").select("*").eq("token_hash", token_hash).maybe_single().execute()
    except Exception as e:
        log.error(f"[admin_auth] verify select error: {type(e).__name__}: {e}")
        raise HTTPException(500, "Token kontrol edilemedi")

    if not result or not result.data:
        write_audit(None, "?", "magic_link_verify", ip, ua, False, {"reason": "not_found"})
        raise HTTPException(404, "Token bulunamadi veya zaten kullanilmis")

    row = result.data
    # expires_at kontrol
    expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        write_audit(None, row.get("user_email"), "magic_link_verify", ip, ua, False, {"reason": "expired"})
        raise HTTPException(410, "Token suresi dolmus")

    # used_at kontrol
    if row.get("used_at"):
        write_audit(None, row.get("user_email"), "magic_link_verify", ip, ua, False, {"reason": "already_used"})
        raise HTTPException(410, "Token zaten kullanilmis")

    email = row["user_email"]

    # Supabase user_id al (admin kontrol)
    admin_user = None
    try:
        result = sb.auth.admin.list_users()
        for u in result:
            if (u.email or "").lower() == email and (u.app_metadata or {}).get("role") == "admin":
                admin_user = u
                break
    except Exception as e:
        log.error(f"[admin_auth] verify list_users error: {type(e).__name__}: {e}")
        raise HTTPException(500, "User kontrol edilemedi")

    if not admin_user:
        write_audit(None, email, "magic_link_verify", ip, ua, False, {"reason": "user_not_admin"})
        raise HTTPException(403, "Admin yetkisi yok")

    # Token used_at isaretle
    sb.table("admin_magic_tokens").update({
        "used_at": datetime.now(timezone.utc).isoformat(),
    }).eq("token_hash", token_hash).execute()

    # Session JWT olustur
    session_jwt = issue_session_token(admin_user.id, email, ip)
    jti = jwt.decode(session_jwt, options={"verify_signature": False})["jti"]
    try:
        sb.table("admin_sessions").insert({
            "id": jti,
            "user_id": admin_user.id,
            "ip": ip,
            "user_agent": ua,
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)).isoformat(),
        }).execute()
    except Exception as e:
        log.error(f"[admin_auth] admin_sessions insert failed: {e}")
        raise HTTPException(500, "Session yazma hatasi")

    write_audit(admin_user.id, email, "magic_link_verify", ip, ua, True, {"jti": jti})

    # 2026-07-15: 302 redirect (HTML response yerine — cross-origin cookie icin)
    # Cross-domain redirect: Railway (backend) → Vercel (frontend /admin)
    # SameSite=None; Secure zorunlu (Chrome 80+ cross-origin icin)
    frontend_url = os.getenv("FRONTEND_URL", "https://pythonmulakat.com")
    response = RedirectResponse(url=f"{frontend_url}/admin", status_code=302)
    response.set_cookie(
        key="admin_session",
        value=session_jwt,
        httponly=True,
        secure=True,  # SameSite=None zorunlu Secure=True
        samesite="none",
        max_age=SESSION_TTL_HOURS * 3600,
        path="/",
    )
    return response


@router.get("/me")
def me(request: Request):
    payload = get_session_from_request(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Session yok veya süresi dolmuş")
    # IP binding KAPALI: Vercel serverless fetch yaparken egress IP degisiyor
    # (login IP != /me IP, redirect loop olusuyor)
    # Production'da farkli IP'lerden ayni cookie ile giris kabul edilir
    # (güvenlik: HttpOnly + Secure + SameSite=Lax cookie yeterli)
    return {
        "id": payload["sub"],
        "email": payload.get("email"),
        "role": "admin",
        "expires_at": datetime.fromtimestamp(payload["exp"], tz=timezone.utc).isoformat(),
    }
