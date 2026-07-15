# backend/auth.py — Production-Ready Email Verification + Username Recovery
# Akış:
#   register → backend 6-haneli kod üretir + Resend ile gönderir
#   verify-email → kullanıcı kodu girer, profile.is_verified=true
#   forgot-password → username doğrula, sonra 6-haneli kod gönder (password reset için)
#   reset-password → kod + yeni şifre ile güncelle
#
# OAuth (Google/GitHub) Supabase üzerinden → /auth/callback?type=oauth → frontend

from fastapi import APIRouter, HTTPException, Request
from services.rate_limiter import AUTH_REGISTER, AUTH_LOGIN
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from supabase_client import get_supabase_admin
from dependencies import get_current_user
import secrets
import datetime
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# ═══════════════════════════════════════════════════════════════
# ─── Schemas ────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

class RegisterPayload(BaseModel):
    username: str = Field(..., min_length=2, max_length=32)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)
    privacy_policy_consent: bool = False


class VerifyPayload(BaseModel):
    email: str
    code: Optional[int] = None


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


class MessageResponse(BaseModel):
    ok: bool
    message: str
    verified: Optional[bool] = None
    expires_in_minutes: Optional[int] = None


class ForgotPasswordStep1Payload(BaseModel):
    """İlk adım: email + username doğrula"""
    email: str
    username: str


class ResetPasswordPayload(BaseModel):
    """Şifre sıfırlama: email + kod + yeni şifre"""
    email: str
    code: int
    new_password: str = Field(..., min_length=6, max_length=128)


# ═══════════════════════════════════════════════════════════════
# ─── Email Service (Resend) ─────────────────────────────────
# ═══════════════════════════════════════════════════════════════

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "mkemal@pythonmulakat.com")


def _send_email(to: str, subject: str, html: str, text: str) -> bool:
    try:
        import requests as http_requests

        response = http_requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": RESEND_FROM_EMAIL,
                "to": [to],
                "subject": subject,
                "html": html,
                "text": text,
            },
            timeout=10,
        )

        if response.status_code in (200, 201):
            logger.info(f"📧 [RESEND] OK → {to} (id: {response.json().get('id', '?')})")
            return True
        else:
            logger.error(f"📧 [RESEND] FAIL → {to}: {response.status_code} {response.text[:200]}")
            return False
    except Exception as e:
        logger.exception(f"Resend HTTP error: {e}")
        return False


def _verification_email_html(username: str, code: str, expires_minutes: int = 15) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#e4e4e7;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:48px 24px;">
<tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background:#13131a;border-radius:20px;overflow:hidden;border:1px solid rgba(255,255,255,0.06);">
<tr><td style="background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 50%,#f59e0b 100%);padding:48px 32px;text-align:center;">
<div style="display:inline-block;width:72px;height:72px;background:rgba(255,255,255,0.18);border-radius:18px;line-height:72px;font-size:40px;">🐍</div>
<h1 style="margin:24px 0 0;color:#fff;font-size:28px;font-weight:800;">PythonMulakat</h1>
<p style="margin:8px 0 0;color:rgba(255,255,255,0.85);font-size:13px;letter-spacing:1px;">MÜLAKAT HAZIRLIK</p>
</td></tr>
<tr><td style="padding:40px 32px;">
<h2 style="margin:0 0 8px;color:#fafafa;font-size:20px;font-weight:700;">Merhaba {username}! 👋</h2>
<p style="margin:0 0 32px;color:#a1a1aa;font-size:15px;line-height:1.6;">Aşağıdaki kodu kullanarak işlemini tamamla.</p>
<div style="background:linear-gradient(135deg,rgba(251,191,36,0.08) 0%,rgba(99,102,241,0.08) 100%);border:1.5px dashed rgba(251,191,36,0.5);border-radius:14px;padding:32px 16px;text-align:center;margin:0 0 32px;">
<p style="margin:0 0 12px;color:#a1a1aa;font-size:11px;letter-spacing:2.5px;text-transform:uppercase;font-weight:700;">Doğrulama Kodun</p>
<div style="font-family:'SF Mono',Menlo,monospace;font-size:44px;font-weight:800;color:#fbbf24;letter-spacing:10px;line-height:1;margin:8px 0;">{code}</div>
<p style="margin:16px 0 0;color:#71717a;font-size:12px;">⏰ {expires_minutes} dakika geçerli</p>
</div>
<p style="margin:0;color:#71717a;font-size:13px;line-height:1.6;">Eğer bu işlemi sen yapmadıysan, bu emaili görmezden gelebilirsin.</p>
</td></tr>
<tr><td style="background:rgba(0,0,0,0.4);padding:18px 32px;text-align:center;border-top:1px solid rgba(255,255,255,0.04);">
<p style="margin:0;color:#52525b;font-size:11px;">© 2026 PythonMulakat · Tüm hakları saklıdır.</p>
</td></tr>
</table>
</td></tr></table>
</body></html>"""


def _verification_email_text(username: str, code: str, expires_minutes: int = 15) -> str:
    return f"""Merhaba {username},

PythonMulakat doğrulama kodun: {code}

Bu kod {expires_minutes} dakika geçerlidir.

Eğer bu işlemi sen yapmadıysan, bu emaili görmezden gelebilirsin.

—
PythonMulakat Ekibi
"""


# ═══════════════════════════════════════════════════════════════
# ─── Helpers ────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

CODE_TTL_MINUTES = 15
MAX_ATTEMPTS_PER_CODE = 5


def _generate_6_digit_code() -> str:
    return f"{secrets.randbelow(900000) + 100000}"


def _ensure_profile(sb_admin, user_id: str, email: str, username: str) -> bool:
    """Profile oluştur (idempotent)."""
    try:
        # maybe_single() yeni SDK'da None dönebiliyor → limit(1)+try/except kullanıyoruz
        try:
            existing = sb_admin.table("profiles").select("id").eq("id", user_id).limit(1).execute()
            rows = (existing.data if existing and getattr(existing, "data", None) else []) or []
        except Exception:
            rows = []

        if rows:
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


def _store_verification_code(sb_admin, email: str, code: str) -> bool:
    """Email bazlı profile'a kodu yaz (register + reset için ortak)."""
    try:
        expires_at = (datetime.datetime.utcnow() + datetime.timedelta(minutes=CODE_TTL_MINUTES)).isoformat()
        result = sb_admin.table("profiles").update({
            "verification_code": code,
            "verification_code_expires_at": expires_at,
            "verification_attempts": 0,
        }).eq("email", email).execute()
        return True
    except Exception as e:
        logger.warning(f"Store code issue: {e}")
        return False


def _verify_code(sb_admin, email: str, code: str, consume: bool = True) -> bool:
    """Kodu kontrol et. consume=True ise başarılıysa kod silinir."""
    try:
        # maybe_single() yeni SDK'da None dönebiliyor → limit(1)+try/except kullanıyoruz
        try:
            result = sb_admin.table("profiles").select(
                "verification_code, verification_code_expires_at, verification_attempts"
            ).eq("email", email).limit(1).execute()
            rows = (result.data if result and getattr(result, "data", None) else []) or []
        except Exception:
            rows = []

        if not rows:
            logger.warning(f"Verify fail: profile not found for {email}")
            return False

        profile = rows[0]
        stored_code = str(profile.get("verification_code", "") or "")
        attempts = int(profile.get("verification_attempts", 0))

        logger.info(f"Verify {email}: stored='{stored_code}' given='{code}' attempts={attempts}")

        # Süre kontrolü
        expires_str = profile.get("verification_code_expires_at", "")
        if expires_str:
            try:
                expires = datetime.datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                if datetime.datetime.now(datetime.timezone.utc) > expires:
                    logger.warning(f"Verify fail: code expired for {email}")
                    return False
            except (ValueError, TypeError):
                pass

        # Attempt limit
        if attempts >= MAX_ATTEMPTS_PER_CODE:
            logger.warning(f"Verify fail: max attempts for {email}")
            return False

        # Kod karşılaştır
        if stored_code != code:
            # Attempt sayısını arttır
            sb_admin.table("profiles").update({
                "verification_attempts": attempts + 1,
            }).eq("email", email).execute()
            logger.warning(f"Verify fail: code mismatch for {email} (given {code}, stored {stored_code})")
            return False

        # Başarılı — kodu temizle (consume)
        if consume:
            sb_admin.table("profiles").update({
                "verification_code": None,
                "verification_code_expires_at": None,
                "verification_attempts": 0,
                "is_verified": True,  # register flow için
            }).eq("email", email).execute()

        logger.info(f"✅ Verify OK: {email}")
        return True
    except Exception as e:
        logger.exception(f"Verify code issue: {e}")
        return False


def _build_auth_response(sb_session, profile: Optional[Dict] = None) -> AuthResponse:
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
            is_verified=(profile or {}).get("is_verified", False),
        ),
    )


# ═══════════════════════════════════════════════════════════════
# ─── Routes ─────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════


@router.post("/register", response_model=MessageResponse)
async def register(request: Request, payload: RegisterPayload):
    """Yeni kullanıcı oluştur + 6-haneli kod gönder."""
    # Rate limit: 3 register/saat/IP
    ip = request.client.host if request.client else "unknown"
    allowed, remaining = AUTH_REGISTER.is_allowed(ip)
    if not allowed:
        raise HTTPException(429, "Çok fazla kayıt denemesi. Lütfen 1 saat sonra tekrar deneyin.")

    try:
        if not payload.privacy_policy_consent:
            raise HTTPException(400, "Gizlilik politikası kabul edilmedi")

        sb_admin = get_supabase_admin()

        # 1. User oluştur (Supabase Admin API — service_role)
        import os as _os_debug
        supabase_url = _os_debug.getenv("SUPABASE_URL", "?")
        supabase_key_prefix = (_os_debug.getenv("SUPABASE_SERVICE_ROLE_KEY") or "?")[:20]
        logger.info(f"🔎 Register attempt: email={payload.email} url={supabase_url} svc={supabase_key_prefix}...")
        try:
            auth_result = sb_admin.auth.admin.create_user({
                "email": payload.email,
                "password": payload.password,
                "email_confirm": False,
                "user_metadata": {"username": payload.username},
            })
            user_id = auth_result.user.id
            logger.info(f"✅ User created: {user_id}")
        except Exception as e:
            error_msg = str(e).lower()
            logger.exception(f"❌ create_user FAILED: email={payload.email} url={supabase_url} svc={supabase_key_prefix}... exc={repr(e)}")
            if "already" in error_msg or "exists" in error_msg:
                raise HTTPException(409, "Bu e-posta zaten kayıtlı")
            # 2026-07-15: User not allowed — Supabase Auth sign-up disabled veya trigger hatası
            if "user not allowed" in error_msg or "not allowed" in error_msg:
                raise HTTPException(
                    403,
                    f"Kayıt şu an kapalı. Supabase Dashboard > Authentication > Sign Up > 'Allow new users to sign up' enable edin. Detay: {str(e)}",
                )
            raise HTTPException(400, f"Kayıt hatası: {str(e)}")

        # 2. Profile oluştur
        _ensure_profile(sb_admin, user_id, payload.email, payload.username)

        # 3. Verification code üret + DB'ye yaz
        code = _generate_6_digit_code()
        _store_verification_code(sb_admin, payload.email, code)

        # 4. Resend ile email gönder
        html = _verification_email_html(payload.username, code)
        text = _verification_email_text(payload.username, code)
        _send_email(
            to=payload.email,
            subject=f"🐍 PythonMulakat — Doğrulama Kodun: {code}",
            html=html,
            text=text,
        )

        logger.info(f"📧 Registered: {payload.email} → code: {code}")

        # 2026-07-14: Dev mode'da kodu response'a ekle (test kolaylığı).
        # Production'da sadece email'e gönderilir, response'da dönmez.
        import os as _os
        is_dev = _os.getenv("APP_ENV", "development").lower() in ("development", "dev", "staging")
        msg = f"Doğrulama kodu {payload.email} adresine gönderildi."
        if is_dev:
            msg += f" (dev: kod {code})"

        return MessageResponse(
            ok=True,
            message=msg,
            verified=False,
            expires_in_minutes=CODE_TTL_MINUTES,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Register endpoint error")
        raise HTTPException(500, f"Kayıt hatası: {str(e)}")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(payload: VerifyPayload):
    """6-haneli kodu doğrula → profile.is_verified=true."""
    try:
        if not payload.code:
            raise HTTPException(400, "Doğrulama kodu gerekli")

        sb_admin = get_supabase_admin()

        # Önce user var mı? (.maybe_single() yeni SDK'da None/exception dönebiliyor — try/except korumalı)
        try:
            result = sb_admin.table("profiles").select("id, email").eq("email", payload.email).limit(1).execute()
            rows = (result.data if result and getattr(result, "data", None) else []) or []
        except Exception as e:
            logger.warning(f"profile lookup failed for {payload.email}: {e}")
            rows = []

        if not rows:
            raise HTTPException(404, "Kullanıcı bulunamadı")

        # Kod doğrula
        ok = _verify_code(sb_admin, payload.email, str(payload.code), consume=True)
        if not ok:
            raise HTTPException(400, "Geçersiz veya süresi dolmuş kod")

        # 2026-07-14 FIX: Supabase auth.users.email_confirmed_at da güncellenmeli
        # (signIn 'Email not confirmed' reddetmesin diye). Yoksa local
        # verification_codes tablosu doğrulanır ama Supabase signIn
        # hâlâ 'email not confirmed' döner.
        user_id = rows[0].get("id")
        if user_id:
            try:
                sb_admin.auth.admin.update_user_by_id(
                    user_id,
                    {"email_confirm": True},
                )
                logger.info(f"✅ Supabase auth.users.email_confirmed_at set: {payload.email}")
            except Exception as e:
                logger.warning(f"⚠️ Supabase email_confirm update failed: {e}")

        logger.info(f"✅ Email verified: {payload.email}")

        return MessageResponse(
            ok=True,
            message="E-posta doğrulandı. Giriş yapabilirsin.",
            verified=True,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Verify endpoint error")
        raise HTTPException(500, f"Doğrulama hatası: {str(e)}")


@router.post("/resend-code", response_model=MessageResponse)
async def resend_code(payload: VerifyPayload):
    """Yeni doğrulama kodu gönder."""
    try:
        sb_admin = get_supabase_admin()

        try:
            result = sb_admin.table("profiles").select("id, username, email, is_verified").eq("email", payload.email).limit(1).execute()
            rows = (result.data if result and getattr(result, "data", None) else []) or []
        except Exception:
            rows = []

        if not rows:
            # Email enumeration koruması: yoksa bile generic mesaj
            return MessageResponse(ok=True, message="Eğer e-posta kayıtlıysa, yeni kod gönderildi.")

        profile = rows[0]

        # Zaten doğrulanmışsa yeni kod gönderme
        if profile.get("is_verified"):
            return MessageResponse(ok=True, message="E-posta zaten doğrulanmış.")

        # Yeni kod üret
        username = profile.get("username", payload.email.split("@")[0])
        new_code = _generate_6_digit_code()
        _store_verification_code(sb_admin, payload.email, new_code)

        html = _verification_email_html(username, new_code)
        text = _verification_email_text(username, new_code)
        _send_email(
            to=payload.email,
            subject=f"🐍 PythonMulakat — Yeni Doğrulama Kodun: {new_code}",
            html=html,
            text=text,
        )

        logger.info(f"📧 Resent code to {payload.email}: {new_code}")

        return MessageResponse(
            ok=True,
            message=f"Yeni kod {payload.email} adresine gönderildi.",
            expires_in_minutes=CODE_TTL_MINUTES,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Resend endpoint error")
        raise HTTPException(500, f"Kod gönderilemedi: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# ─── Login (email doğrulanmış olmalı) ───────────────────────
# ═══════════════════════════════════════════════════════════════


@router.post("/login", response_model=AuthResponse)
async def login(request: Request, payload: LoginPayload):
    # Rate limit: 5 login/dakika/IP
    ip = request.client.host if request.client else "unknown"
    allowed, remaining = AUTH_LOGIN.is_allowed(ip)
    if not allowed:
        raise HTTPException(429, "Çok fazla giriş denemesi. Lütfen 1 dakika sonra tekrar deneyin.")
    try:
        sb_admin = get_supabase_admin()

        # 1. Supabase'ten session al
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
            raise HTTPException(401, f"Giriş hatası: {str(e)}")

        # 2. Profile bilgisi
        profile = None
        try:
            # maybe_single() yeni SDK'da None dönebiliyor → limit(1)+try/except kullanıyoruz
            result = sb_admin.table("profiles").select("*").eq("id", user.id).limit(1).execute()
            rows = (result.data if result and getattr(result, "data", None) else []) or []
            profile = rows[0] if rows else None
        except Exception as e:
            logger.warning(f"Profile fetch error: {e}")

        # 3. Email doğrulama kontrolü (is_verified alanı)
        # OAuth kullanıcılar için is_verified=True kabul edilir
        if profile and not profile.get("is_verified", False):
            # Kullanıcı daha önce register olmuş ama verify etmemiş
            # Email gönderimini tetikleyelim (yeniden)
            try:
                username = profile.get("username", payload.email.split("@")[0])
                code = _generate_6_digit_code()
                _store_verification_code(sb_admin, payload.email, code)
                html = _verification_email_html(username, code)
                text = _verification_email_text(username, code)
                _send_email(
                    to=payload.email,
                    subject=f"🐍 PythonMulakat — Doğrulama Kodun: {code}",
                    html=html,
                    text=text,
                )
            except Exception as e:
                logger.warning(f"Auto-resend on login failed: {e}")

            raise HTTPException(403, "E-posta adresin doğrulanmamış. E-postana gönderilen kodu kullan.")

        return _build_auth_response(session, profile)
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

        profile = None
        try:
            # maybe_single() yeni SDK'da None dönebiliyor → limit(1)+try/except kullanıyoruz
            result = sb_admin.table("profiles").select("*").eq("id", user_id).limit(1).execute()
            rows = (result.data if result and getattr(result, "data", None) else []) or []
            profile = rows[0] if rows else None
        except Exception as e:
            logging.warning("me.profile.fetch_failed user=%s err=%s", user_id, e)

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
        except Exception as e:
            logging.warning("me.attempts.fetch_failed user=%s err=%s", user_id, e)

        return {
            "id": user_id,
            "email": user.get("email"),
            "username": (profile or {}).get("username", user.get("email", "").split("@")[0]),
            "is_verified": (profile or {}).get("is_verified", False),
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


