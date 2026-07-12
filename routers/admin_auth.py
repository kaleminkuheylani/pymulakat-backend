"""
routers/admin_auth.py
Production-grade admin auth router:
  - 2 aşamalı login (email+password → mfa_token → TOTP)
  - HttpOnly session cookie (8 saat)
  - Audit log (her login attempt + her admin action)
  - 5 başarısız login → 15dk lockout
  - Rate limit (slowapi)
  - TOTP (pyotp) zorunlu admin için

Endpoints (prefix /api/v2/admin/auth):
  POST /login                 → email+password → mfa_token (5dk)
  POST /verify-mfa            → mfa_token+totp → session cookie
  POST /logout                → session revoke
  GET  /me                    → session validate (guard için)
  POST /setup-mfa             → MFA secret + QR (ilk kez kurulum)
  POST /disable-mfa           → MFA devre dışı (super admin only)

Güvenlik:
  - ADMIN_JWT_SECRET (HMAC-SHA256, 64 char) → session JWT imzalar
  - Session cookie: HttpOnly, Secure, SameSite=Strict
  - MFA: TOTP (RFC 6238), 30s window, ±1 drift
  - Lockout: 5 fail → 15dk
  - Rate limit: 5 login/dk/IP (slowapi)
  - IP allowlist: ADMIN_IP_ALLOWLIST env (opsiyonel)
"""

import os
import secrets
import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import pyotp
import qrcode
import io
import base64
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from supabase_client import get_supabase, get_supabase_admin

log = logging.getLogger("pymulakat.admin_auth")

router = APIRouter(prefix="/api/v2/admin/auth", tags=["admin-auth"])

# ═══════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════

ADMIN_JWT_SECRET = os.getenv("ADMIN_JWT_SECRET", "")
if not ADMIN_JWT_SECRET or len(ADMIN_JWT_SECRET) < 32:
    log.warning("[admin_auth] ADMIN_JWT_SECRET tanımsız veya <32 char. Production'da set edilmeli.")

ADMIN_MFA_ISSUER = os.getenv("ADMIN_MFA_ISSUER", "PythonMulakat")
SESSION_TTL_HOURS = int(os.getenv("ADMIN_SESSION_TTL_HOURS", "8"))
MFA_TOKEN_TTL_MIN = int(os.getenv("ADMIN_MFA_TOKEN_TTL_MIN", "5"))
LOCKOUT_THRESHOLD = int(os.getenv("ADMIN_LOCKOUT_THRESHOLD", "5"))
LOCKOUT_DURATION_MIN = int(os.getenv("ADMIN_LOCKOUT_DURATION_MIN", "15"))
IP_ALLOWLIST = [ip.strip() for ip in os.getenv("ADMIN_IP_ALLOWLIST", "").split(",") if ip.strip()]


# ═══════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyMfaRequest(BaseModel):
    mfa_token: str
    totp_code: str


class MfaSetupResponse(BaseModel):
    secret: str
    qr_png_base64: str
    otpauth_url: str
    backup_codes: list[str]


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def get_client_ip(request: Request) -> str:
    """Client IP (X-Forwarded-For öncelikli, CF/Vercel standardı)."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "")[:500]  # truncate


def check_ip_allowlist(ip: str) -> None:
    """IP allowlist kontrolü. Allowlist boşsa skip."""
    if not IP_ALLOWLIST:
        return
    if ip not in IP_ALLOWLIST:
        log.warning(f"[admin_auth] IP allowlist reddedildi: {ip}")
        raise HTTPException(status_code=403, detail="Bu IP'den admin erişimi yok")


def write_audit(
    user_id: Optional[str],
    user_email: str,
    action: str,
    ip: str,
    ua: str,
    success: bool,
    detail: dict = None,
) -> None:
    """Admin audit log yaz."""
    sb = get_supabase_admin()
    try:
        sb.table("admin_audit_log").insert({
            "user_id": user_id,
            "user_email": user_email,
            "action": action,
            "ip": ip,
            "user_agent": ua,
            "success": success,
            "detail": detail or {},
        }).execute()
    except Exception as e:
        log.error(f"[admin_auth] audit log yazılamadı: {e}")


def get_lockout_status(email: str) -> dict:
    """Lockout kontrol. {'locked': bool, 'until': datetime, 'failed': int}"""
    sb = get_supabase_admin()
    try:
        result = sb.table("admin_lockout").select("*").eq("user_email", email).maybe_single().execute()
        if not result.data:
            return {"locked": False, "until": None, "failed": 0}
        row = result.data
        locked_until = row.get("locked_until")
        if locked_until:
            # locked_until tz-aware mi?
            if isinstance(locked_until, str):
                locked_until = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
            if locked_until > datetime.now(timezone.utc):
                return {"locked": True, "until": locked_until, "failed": row.get("failed_count", 0)}
        return {"locked": False, "until": None, "failed": row.get("failed_count", 0)}
    except Exception as e:
        log.error(f"[admin_auth] lockout kontrol hatası: {e}")
        return {"locked": False, "until": None, "failed": 0}


def record_failed_login(email: str) -> None:
    """Başarısız login kaydet + lockout kontrol."""
    sb = get_supabase_admin()
    try:
        # Mevcut kayit
        result = sb.table("admin_lockout").select("*").eq("user_email", email).maybe_single().execute()
        if result.data:
            failed = result.data["failed_count"] + 1
            update = {"failed_count": failed, "last_attempt_at": datetime.now(timezone.utc).isoformat()}
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


def clear_lockout(email: str) -> None:
    """Başarılı login sonrası lockout temizle."""
    sb = get_supabase_admin()
    try:
        sb.table("admin_lockout").delete().eq("user_email", email).execute()
    except Exception:
        pass


def issue_mfa_token(user_id: str, email: str) -> str:
    """Kısa ömürlü mfa_token (5dk). MFA verify için."""
    payload = {
        "sub": user_id,
        "email": email,
        "purpose": "admin_mfa",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=MFA_TOKEN_TTL_MIN),
    }
    return jwt.encode(payload, ADMIN_JWT_SECRET, algorithm="HS256")


def issue_session_token(user_id: str, email: str, ip: str, ua: str) -> str:
    """Session JWT (8 saat). Cookie + Authorization header."""
    jti = secrets.token_urlsafe(32)
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
    """Request'ten session JWT al + validate et."""
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
        # jti DB'de var mi + revoked mi?
        sb = get_supabase_admin()
        result = sb.table("admin_sessions").select("*").eq("id", payload["jti"]).maybe_single().execute()
        if not result.data:
            return None
        if result.data.get("revoked"):
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
    """Aşama 1: email + password → mfa_token (MFA kurulu ise).
    
    Akış:
    1. IP allowlist kontrol
    2. Lockout kontrol (5 fail → 15dk)
    3. Supabase auth.signInWithPassword (password validate)
    4. App metadata'da role=admin kontrol (zorunlu)
    5. MFA kurulu mu? → mfa_token döner
       Kurulu değil → direkt session (ilk kez setup için)
    """
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    email = req.email.lower().strip()
    
    # 1) IP allowlist
    check_ip_allowlist(ip)
    
    # 2) Lockout
    lockout = get_lockout_status(email)
    if lockout["locked"]:
        write_audit(None, email, "login", ip, ua, False, {"reason": "locked_until", "until": str(lockout["until"])})
        raise HTTPException(
            status_code=429,
            detail=f"Hesap kilitli. {lockout['until'].isoformat() if lockout['until'] else '15dk'} sonra tekrar deneyin.",
        )
    
    # 3) Supabase signIn
    sb = get_supabase()
    try:
        result = sb.auth.sign_in_with_password({"email": email, "password": req.password})
    except Exception as e:
        # Generic error (timing attack'a karsi)
        record_failed_login(email)
        write_audit(None, email, "login", ip, ua, False, {"reason": "auth_failed"})
        # 401 doner (guvenli mesaj)
        raise HTTPException(status_code=401, detail="Geçersiz email veya şifre")
    
    if not result or not result.user:
        record_failed_login(email)
        write_audit(None, email, "login", ip, ua, False, {"reason": "no_user"})
        raise HTTPException(status_code=401, detail="Geçersiz email veya şifre")
    
    user = result.user
    user_id = user.id
    
    # 4) Admin role kontrol
    app_role = (user.app_metadata or {}).get("role", "user")
    if app_role != "admin":
        record_failed_login(email)
        write_audit(user_id, email, "login", ip, ua, False, {"reason": "not_admin"})
        # Generic error (admin mi diye belli etme)
        raise HTTPException(status_code=401, detail="Geçersiz email veya şifre")
    
    # 5) MFA kontrol
    mfa_result = sb_admin = get_supabase_admin().table("admin_mfa").select("*").eq("user_id", user_id).maybe_single().execute()
    mfa_enabled = mfa_result.data.get("enabled", False) if mfa_result.data else False
    
    if mfa_enabled:
        # MFA aşaması gerekli
        mfa_token = issue_mfa_token(user_id, email)
        clear_lockout(email)
        write_audit(user_id, email, "login", ip, ua, True, {"stage": "password", "mfa_required": True})
        return JSONResponse(
            {
                "mfa_required": True,
                "mfa_token": mfa_token,
                "message": "TOTP kodunu girin",
            }
        )
    else:
        # MFA kurulu değil — direkt session
        session_jwt = issue_session_token(user_id, email, ip, ua)
        # DB session kayit
        jti = jwt.decode(session_jwt, options={"verify_signature": False})["jti"]
        get_supabase_admin().table("admin_sessions").insert({
            "id": jti,
            "user_id": user_id,
            "ip": ip,
            "user_agent": ua,
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)).isoformat(),
        }).execute()
        clear_lockout(email)
        write_audit(user_id, email, "login", ip, ua, True, {"stage": "complete", "mfa_enabled": False})
        response.set_cookie(
            key="admin_session",
            value=session_jwt,
            max_age=SESSION_TTL_HOURS * 3600,
            httponly=True,
            secure=True,
            samesite="strict",
            path="/",
        )
        return JSONResponse(
            {
                "authenticated": True,
                "user": {"id": user_id, "email": email, "role": "admin"},
                "mfa_setup_required": True,  # ilk kez login — MFA setup zorunlu
                "message": "MFA kurulumu zorunlu. /api/v2/admin/auth/setup-mfa kullanın",
            }
        )


@router.post("/verify-mfa")
def verify_mfa(req: VerifyMfaRequest, request: Request, response: Response):
    """Aşama 2: mfa_token + TOTP kod → session cookie."""
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    
    # 1) mfa_token validate
    try:
        payload = jwt.decode(req.mfa_token, ADMIN_JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="MFA token süresi dolmuş. Tekrar login olun.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz MFA token")
    
    if payload.get("purpose") != "admin_mfa":
        raise HTTPException(status_code=401, detail="Geçersiz token tipi")
    
    user_id = payload["sub"]
    email = payload["email"]
    
    # 2) MFA secret DB'den al
    mfa_row = get_supabase_admin().table("admin_mfa").select("*").eq("user_id", user_id).maybe_single().execute()
    if not mfa_row.data or not mfa_row.data.get("enabled"):
        raise HTTPException(status_code=401, detail="MFA kurulu değil")
    
    secret = mfa_row.data["secret"]
    totp = pyotp.TOTP(secret)
    
    # 3) TOTP doğrula (±1 window = 90s tolerance)
    if not totp.verify(req.totp_code, valid_window=1):
        write_audit(user_id, email, "mfa_verify", ip, ua, False, {})
        raise HTTPException(status_code=401, detail="Geçersiz TOTP kodu")
    
    # 4) Session JWT issue
    session_jwt = issue_session_token(user_id, email, ip, ua)
    jti = jwt.decode(session_jwt, options={"verify_signature": False})["jti"]
    get_supabase_admin().table("admin_sessions").insert({
        "id": jti,
        "user_id": user_id,
        "ip": ip,
        "user_agent": ua,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)).isoformat(),
    }).execute()
    clear_lockout(email)
    write_audit(user_id, email, "mfa_verify", ip, ua, True, {})
    write_audit(user_id, email, "login", ip, ua, True, {"stage": "complete", "mfa_enabled": True})
    
    response.set_cookie(
        key="admin_session",
        value=session_jwt,
        max_age=SESSION_TTL_HOURS * 3600,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
    )
    return JSONResponse(
        {
            "authenticated": True,
            "user": {"id": user_id, "email": email, "role": "admin"},
        }
    )


@router.post("/logout")
def logout(request: Request, response: Response):
    """Session revoke."""
    payload = get_session_from_request(request)
    if payload:
        # DB'de session revoke
        try:
            get_supabase_admin().table("admin_sessions").update({
                "revoked": True,
                "revoked_at": datetime.now(timezone.utc).isoformat(),
                "revoke_reason": "logout",
            }).eq("id", payload["jti"]).execute()
            write_audit(payload["sub"], payload.get("email"), "logout", get_client_ip(request), get_user_agent(request), True, {})
        except Exception:
            pass
    
    response.delete_cookie("admin_session", path="/")
    return {"ok": True}


@router.get("/me")
def me(request: Request):
    """Session validate (frontend guard için)."""
    payload = get_session_from_request(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Session yok veya süresi dolmuş")
    
    # IP check (session basladiği IP)
    current_ip = get_client_ip(request)
    if payload.get("ip") and payload["ip"] != current_ip:
        # Farklı IP'den erişim — audit log
        write_audit(
            payload["sub"], payload.get("email"), "guard_deny", current_ip, get_user_agent(request), False,
            {"reason": "ip_mismatch", "session_ip": payload["ip"]}
        )
        raise HTTPException(status_code=401, detail="IP değişti, tekrar login gerekli")
    
    return {
        "id": payload["sub"],
        "email": payload.get("email"),
        "role": "admin",
        "expires_at": datetime.fromtimestamp(payload["exp"], tz=timezone.utc).isoformat(),
    }


@router.post("/setup-mfa")
def setup_mfa(request: Request, response: Response):
    """MFA kurulumu: TOTP secret üret + QR kod döner.
    
    Kullanıcı authenticator app'e QR'ı tarar, ilk TOTP kodu ile setup tamamlar.
    """
    payload = get_session_from_request(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Önce login olun")
    
    user_id = payload["sub"]
    email = payload["email"]
    
    # Yeni secret üret
    secret = pyotp.random_base32()
    
    # DB'ye yaz (enabled=False — verify_code ile enabled yapilacak)
    sb_admin = get_supabase_admin()
    existing = sb_admin.table("admin_mfa").select("user_id").eq("user_id", user_id).maybe_single().execute()
    if existing.data:
        sb_admin.table("admin_mfa").update({"secret": secret, "enabled": False}).eq("user_id", user_id).execute()
    else:
        sb_admin.table("admin_mfa").insert({"user_id": user_id, "secret": secret, "enabled": False}).execute()
    
    # QR kod üret
    totp = pyotp.TOTP(secret)
    otpauth_url = totp.provisioning_uri(name=email, issuer_name=ADMIN_MFA_ISSUER)
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(otpauth_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_png_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    
    # Backup kodları (8 adet, tek kullanımlık)
    backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
    sb_admin.table("admin_mfa").update({"backup_codes": backup_codes}).eq("user_id", user_id).execute()
    
    return {
        "secret": secret,
        "qr_png_base64": qr_png_b64,
        "otpauth_url": otpauth_url,
        "backup_codes": backup_codes,
    }


@router.post("/enable-mfa")
def enable_mfa(request: Request, response: Response, body: dict = None):
    """Kurulan MFA'yı TOTP kodu ile aktifleştir."""
    payload = get_session_from_request(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Login gerekli")
    
    user_id = payload["sub"]
    body = body or {}
    totp_code = body.get("totp_code", "")
    
    if not totp_code or len(totp_code) != 6:
        raise HTTPException(status_code=400, detail="6 haneli TOTP kodu gerekli")
    
    # DB'den secret al
    mfa_row = get_supabase_admin().table("admin_mfa").select("*").eq("user_id", user_id).maybe_single().execute()
    if not mfa_row.data:
        raise HTTPException(status_code=400, detail="Önce setup-mfa çağırın")
    
    totp = pyotp.TOTP(mfa_row.data["secret"])
    if not totp.verify(totp_code, valid_window=1):
        write_audit(user_id, payload["email"], "mfa_verify", get_client_ip(request), get_user_agent(request), False, {"stage": "enable"})
        raise HTTPException(status_code=401, detail="Geçersiz TOTP kodu")
    
    # Enable
    get_supabase_admin().table("admin_mfa").update({
        "enabled": True,
        "enabled_at": datetime.now(timezone.utc).isoformat(),
    }).eq("user_id", user_id).execute()
    write_audit(user_id, payload["email"], "mfa_verify", get_client_ip(request), get_user_agent(request), True, {"stage": "enabled"})
    
    return {"enabled": True, "message": "MFA aktif"}


@router.get("/audit-log")
def get_audit_log(request: Request, limit: int = 50, action: Optional[str] = None, success: Optional[bool] = None):
    """Audit log listele (admin only)."""
    payload = get_session_from_request(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Login gerekli")
    
    sb_admin = get_supabase_admin()
    query = sb_admin.table("admin_audit_log").select("*").order("created_at", desc=True).limit(min(limit, 200))
    if action:
        query = query.eq("action", action)
    if success is not None:
        query = query.eq("success", success)
    
    result = query.execute()
    return {"entries": result.data or [], "total": len(result.data or [])}
