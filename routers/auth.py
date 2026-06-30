# backend/auth.py — Production-grade, Supabase-native email verification
# Akış: register → Supabase confirm email → callback → login

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from supabase_client import get_supabase_admin
from dependencies import get_current_user
import logging
import os

# ═══════════════════════════════════════════════════════════════
# ─── Logging ───────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# ─── Schemas ────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

class RegisterPayload(BaseModel):
    username: str = Field(..., min_length=2, max_length=32)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)
    privacy_policy_consent: bool = False


class LoginPayload(BaseModel):
    email: str
    password: str


class UserInfo(BaseModel):
    id: str
    email: str
    username: str
    is_verified: bool


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: Optional[int] = None
    token_type: str = "bearer"
    user: UserInfo
    is_verified: Optional[bool] = None  # Backward compat


class MessageResponse(BaseModel):
    ok: bool
    message: str


# ═══════════════════════════════════════════════════════════════
# ─── Helpers ────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

def _ensure_profile(sb_admin, user_id: str, email: str, username: str) -> bool:
    """Profile oluştur (idempotent)."""
    try:
        existing = sb_admin.table("profiles").select("id").eq("id", user_id).maybe_single().execute()
        if existing.data:
            return True
        sb_admin.table("profiles").insert({
            "id": user_id,
            "username": username,
            "email": email,
            "is_verified": False,
            "points": 0,
        }).execute()
        return True
    except Exception as e:
        logger.warning(f"Profile creation issue: {e}")
        return False


def _is_supabase_verified(user) -> bool:
    """Supabase user.email_confirmed_at varsa verified say."""
    if not user:
        return False
    return bool(getattr(user, "email_confirmed_at", None))


def _sync_profile_verified(sb_admin, user_id: str, verified: bool) -> None:
    """profile.is_verified alanını Supabase durumuyla senkronize et."""
    try:
        sb_admin.table("profiles").update({"is_verified": verified}).eq("id", user_id).execute()
    except Exception as e:
        logger.warning(f"Profile sync issue: {e}")


def _build_auth_response(sb_session, profile: Optional[Dict], user_verified: bool) -> AuthResponse:
    user = sb_session.user
    username = (profile or {}).get("username", user.email.split("@")[0])
    return AuthResponse(
        access_token=sb_session.access_token,
        refresh_token=sb_session.refresh_token,
        expires_at=getattr(sb_session, "expires_at", None),
        user=UserInfo(
            id=user.id,
            email=user.email,
            username=username,
            is_verified=user_verified,
        ),
        is_verified=user_verified,
    )


# ═══════════════════════════════════════════════════════════════
# ─── Router ──────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse)
async def register(payload: RegisterPayload):
    """
    Register — Supabase user oluşturur.
    Email doğrulama Supabase tarafından yönetilir:
      - email_confirm=False → Supabase "Confirm signup" email'i gönderir
      - Kullanıcı linke tıklar → Supabase user.email_confirmed_at set eder
      - /auth/me bu değeri profile.is_verified olarak yansıtır
    """
    try:
        if not payload.privacy_policy_consent:
            raise HTTPException(400, "Gizlilik politikası kabul edilmedi")

        sb_admin = get_supabase_admin()
        app_url = os.environ.get("APP_URL", "https://www.pythonmulakat.com")

        # 1. User oluştur (service_role bypass)
        try:
            auth_result = sb_admin.auth.admin.create_user({
                "email": payload.email,
                "password": payload.password,
                "email_confirm": False,  # Supabase confirmation email göndersin
                "user_metadata": {"username": payload.username},
            })
            user_id = auth_result.user.id
            logger.info(f"✅ User created: {user_id}")
        except Exception as admin_err:
            error_msg = str(admin_err).lower()
            if "already" in error_msg or "exists" in error_msg:
                raise HTTPException(409, "Bu e-posta zaten kayıtlı")
            raise HTTPException(400, f"Kayıt hatası: {str(admin_err)}")

        # 2. Profile oluştur
        _ensure_profile(sb_admin, user_id, payload.email, payload.username)

        # 3. Supabase'in gönderdiği confirmation email'i tetiklemek için
        #    admin.invite_user veya resend ile tetikle.
        #    create_user email_confirm=False ile Supabase zaten mail atıyor,
        #    ama bazı projelerde tetiklenmiyor — bu yüzden emin olmak için resend.
        try:
            from supabase_client import get_supabase_admin as _ga
            _ga().auth.admin.generate_link({
                "type": "signup",
                "email": payload.email,
                "options": {"redirect_to": f"{app_url}/auth/callback?type=signup"},
            })
        except Exception as link_err:
            # generate_link başarısız olsa bile create_user ile user oluştu,
            # Supabase zaten confirmation email göndermiş olmalı.
            logger.warning(f"generate_link fallback: {link_err}")

        return MessageResponse(
            ok=True,
            message="Kayıt başarılı. E-postana gönderilen doğrulama linkine tıkla.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Register endpoint error")
        raise HTTPException(500, f"Kayıt hatası: {str(e)}")


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginPayload):
    """
    Login — Supabase session döndür.
    Email doğrulanmamışsa 403 + email_verified=False ile döner.
    """
    try:
        sb_admin = get_supabase_admin()

        try:
            auth_result = sb_admin.auth.sign_in_with_password({
                "email": payload.email,
                "password": payload.password,
            })
            session = auth_result.session
            user = auth_result.user
        except Exception as e:
            error_msg = str(e).lower()
            if "invalid" in error_msg or "credentials" in error_msg:
                raise HTTPException(401, "Geçersiz e-posta veya şifre")
            if "email not confirmed" in error_msg or "not confirmed" in error_msg:
                # Frontend bu durumda Supabase'in "resend confirmation" 
                # akışını kullanabilir
                raise HTTPException(403, "E-posta adresin doğrulanmamış. Lütfen e-postandaki linke tıkla.")
            raise HTTPException(401, f"Giriş hatası: {str(e)}")

        # Supabase user verified mi?
        user_verified = _is_supabase_verified(user)

        # Profile bilgisi
        profile = None
        try:
            result = sb_admin.table("profiles").select("*").eq("id", user.id).maybe_single().execute()
            profile = result.data
        except Exception as e:
            logger.warning(f"Profile fetch error: {e}")

        # profile.is_verified ile Supabase durumunu senkronize et
        if profile is not None:
            profile_verified = bool(profile.get("is_verified", False))
            if profile_verified != user_verified:
                _sync_profile_verified(sb_admin, user.id, user_verified)

        return _build_auth_response(session, profile, user_verified)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Login endpoint error")
        raise HTTPException(500, f"Giriş hatası: {str(e)}")


@router.post("/logout", response_model=MessageResponse)
async def logout():
    return MessageResponse(ok=True, message="Çıkış başarılı")


@router.get("/me")
async def get_me(request: Request):
    """Mevcut kullanıcı + stats."""
    try:
        user = await get_current_user(request)
        if not user:
            raise HTTPException(401, "Token gerekli")

        sb_admin = get_supabase_admin()
        user_id = user["id"]

        # Supabase user üzerinden email verified durumunu öğren
        user_verified = bool(user.get("email_confirmed_at"))

        profile = None
        try:
            result = sb_admin.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
            profile = result.data
        except Exception:
            pass

        # profile.is_verified ile Supabase durumunu senkronize et
        if profile is not None:
            profile_verified = bool(profile.get("is_verified", False))
            if profile_verified != user_verified:
                _sync_profile_verified(sb_admin, user_id, user_verified)

        total_attempts = success_count = fail_count = points = avg_time_ms = 0
        try:
            attempts = sb_admin.table("interview_attempts").select(
                "passed_tests, total_tests, success, execution_time_ms"
            ).eq("user_id", user_id).execute().data or []
            total_attempts = len(attempts)
            success_count = sum(1 for a in attempts if a.get("success"))
            fail_count = total_attempts - success_count
            points = sum(a.get("passed_tests", 0) * 10 for a in attempts if a.get("success"))
            if total_attempts > 0:
                avg_time_ms = sum(a.get("execution_time_ms", 0) for a in attempts) / total_attempts
        except Exception:
            pass

        return {
            "id": user_id,
            "email": user.get("email"),
            "username": (profile or {}).get("username", user.get("email", "").split("@")[0]),
            "is_verified": user_verified,
            "points": points,
            "total_attempts": total_attempts,
            "success_count": success_count,
            "fail_count": fail_count,
            "success_rate": round((success_count / total_attempts * 100) if total_attempts else 0),
            "solution_average_time": int(avg_time_ms / 1000),
            "solution_average_time_ms": int(avg_time_ms),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/resend-confirmation", response_model=MessageResponse)
async def resend_confirmation(payload: LoginPayload):
    """
    Yeni confirmation email gönder.
    Kullanıcı email'i confirm etmediyse bu endpoint ile tekrar tetiklenir.
    Güvenlik: email kayıtlı olsun olmasın aynı mesajı döner (email enumeration koruması).
    """
    try:
        sb_admin = get_supabase_admin()
        app_url = os.environ.get("APP_URL", "https://www.pythonmulakat.com")

        try:
            # Önce user var mı kontrol et
            user_result = sb_admin.auth.admin.list_users()
            user_exists = any(u.email == payload.email for u in (user_result or []))

            if user_exists:
                # generate_link ile yeni confirmation email tetikle
                sb_admin.auth.resend({
                    "type": "signup",
                    "email": payload.email,
                    "options": {"redirect_to": f"{app_url}/auth/callback?type=signup"},
                })
        except Exception as e:
            logger.warning(f"resend confirmation error (gizli): {e}")
            # Hata olsa bile generic mesaj dön

        # Email enumeration koruması — her durumda aynı mesaj
        return MessageResponse(
            ok=True,
            message="Eğer bu e-posta kayıtlıysa, doğrulama linki gönderildi.",
        )
    except Exception as e:
        logger.exception("Resend confirmation error")
        # Hata olsa bile generic mesaj
        return MessageResponse(
            ok=True,
            message="Eğer bu e-posta kayıtlıysa, doğrulama linki gönderildi.",
        )