"""
routers/admin_profile.py
Profile-based admin auth — Supabase signIn bagimliligi YOK.

Endpointler (prefix /api/v2/admin/profile):
  POST /seed           → service_role ile ilk admin user olustur
  POST /auth/login     → email + password → session cookie (kendi DB'miz)
  GET  /auth/me        → session validate

Avantaj:
  - auth.users bagimliligi YOK
  - Supabase signIn rate limit YOK
  - Kendi sifre hash + lockout
  - profiles tablosu, is_admin kolonu ile yalitilmis
"""

import os
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import jwt
import bcrypt
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from supabase_client import get_supabase_admin

log = logging.getLogger("pymulakat.admin_profile")

router = APIRouter(prefix="/api/v2/admin/profile", tags=["admin-profile"])

ADMIN_JWT_SECRET = os.getenv("ADMIN_JWT_SECRET", "pymulakat-admin-jwt-secret-DO-NOT-USE-IN-PRODUCTION-32+chars")
SESSION_TTL_HOURS = int(os.getenv("ADMIN_SESSION_TTL_HOURS", "8"))
LOCKOUT_THRESHOLD = int(os.getenv("ADMIN_LOCKOUT_THRESHOLD", "5"))
LOCKOUT_DURATION_MIN = int(os.getenv("ADMIN_LOCKOUT_DURATION_MIN", "15"))


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SeedRequest(BaseModel):
    email: EmailStr
    password: str


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def issue_session_token(profile_id: str, email: str) -> str:
    jti = str(uuid.uuid4())
    payload = {
        "sub": profile_id,
        "email": email,
        "jti": jti,
        "type": "profile",  # Supabase session'lardan ayirt etmek icin
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS),
    }
    return jwt.encode(payload, ADMIN_JWT_SECRET, algorithm="HS256")


def get_profile_session(request: Request) -> Optional[dict]:
    auth = request.headers.get("authorization", "")
    token = ""
    if auth.startswith("Bearer "):
        token = auth[7:]
    if not token:
        token = request.cookies.get("admin_session", "")
    if not token:
        return None

    try:
        payload = jwt.decode(token, ADMIN_JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "profile":
            return None
        # Profile hala var mi + admin mi?
        sb = get_supabase_admin()
        result = sb.table("profiles").select("id, email, is_admin").eq("id", payload["sub"]).maybe_single().execute()
        if not result.data or not result.data.get("is_admin"):
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@router.post("/seed")
def seed_admin(req: SeedRequest, authorization: str = ""):
    """Service_role key ile ilk admin user olustur.
    Idempotent: email zaten varsa sifreyi guncelle.
    """
    expected = f"Bearer {os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')}"
    if not os.getenv("SUPABASE_SERVICE_ROLE_KEY") or authorization != expected:
        raise HTTPException(401, "service_role key gerekli")

    sb = get_supabase_admin()
    password_hash = bcrypt.hashpw(req.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    result = sb.table("profiles").select("id").eq("email", req.email).maybe_single().execute()
    if result.data:
        # Update
        sb.table("profiles").update({
            "password_hash": password_hash,
            "is_admin": True,
        }).eq("id", result.data["id"]).execute()
        return {"ok": True, "action": "updated", "email": req.email, "id": result.data["id"]}
    else:
        # Insert
        new_id = str(uuid.uuid4())
        sb.table("profiles").insert({
            "id": new_id,
            "email": req.email,
            "password_hash": password_hash,
            "is_admin": True,
            "display_name": req.email.split("@")[0],
        }).execute()
        return {"ok": True, "action": "created", "email": req.email, "id": new_id}


@router.post("/auth/login")
def login(req: LoginRequest, request: Request):
    """Email + password → session cookie (kendi DB'miz)."""
    email = req.email.lower().strip()
    sb = get_supabase_admin()
    ip = get_client_ip(request)

    # 1) Profile bul
    result = sb.table("profiles").select("*").eq("email", email).maybe_single().execute()
    if not result.data:
        raise HTTPException(401, "Geçersiz email veya şifre")
    profile = result.data

    if not profile.get("is_admin"):
        raise HTTPException(401, "Bu hesap admin değil")

    # 2) Lockout kontrol
    if profile.get("failed_count", 0) >= LOCKOUT_THRESHOLD:
        last_attempt = profile.get("last_login_at")
        if last_attempt:
            try:
                if isinstance(last_attempt, str):
                    last_dt = datetime.fromisoformat(last_attempt.replace("Z", "+00:00"))
                    if last_dt > datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_DURATION_MIN):
                        raise HTTPException(429, "Hesap kilitli. 15dk sonra tekrar deneyin.")
            except HTTPException:
                raise
            except Exception:
                pass

    # 3) Password kontrol
    stored_hash = profile.get("password_hash", "")
    if not stored_hash or not bcrypt.checkpw(req.password.encode("utf-8"), stored_hash.encode("utf-8")):
        # Basarisiz — failed_count++
        sb.table("profiles").update({
            "failed_count": (profile.get("failed_count", 0) or 0) + 1,
            "last_login_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", profile["id"]).execute()
        raise HTTPException(401, "Geçersiz email veya şifre")

    # 4) Basarili — failed_count reset + last_login_at update
    sb.table("profiles").update({
        "failed_count": 0,
        "last_login_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", profile["id"]).execute()

    # 5) Session JWT + admin_sessions tablosu
    session_jwt = issue_session_token(profile["id"], email)
    jti = jwt.decode(session_jwt, options={"verify_signature": False})["jti"]
    sb.table("admin_sessions").insert({
        "id": jti,
        "user_id": profile["id"],
        "ip": ip,
        "user_agent": request.headers.get("user-agent", "")[:500],
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)).isoformat(),
    }).execute()

    # 6) Set-Cookie (hard header — JSONResponse guvenilir)
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
            "user": {"id": profile["id"], "email": email, "role": "admin", "source": "profile"},
        },
        headers={"Set-Cookie": set_cookie_header},
    )


@router.get("/auth/me")
def me(request: Request):
    payload = get_profile_session(request)
    if not payload:
        raise HTTPException(401, "Session yok veya süresi dolmuş")
    return {
        "id": payload["sub"],
        "email": payload.get("email"),
        "role": "admin",
        "source": "profile",
        "expires_at": datetime.fromtimestamp(payload["exp"], tz=timezone.utc).isoformat(),
    }
