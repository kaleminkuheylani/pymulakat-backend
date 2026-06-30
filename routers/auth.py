# backend/auth.py — SÜRDÜRÜLEBİLİR PRODUCTION VERSİYON
# Email gönderimi entegre, minimal, sadece inline HTML

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from supabase_client import get_supabase_admin
from dependencies import get_current_user
import secrets
import datetime
import logging
import os

# ═══════════════════════════════════════════════════════════════
# ─── Logging ────────────────────────────────────────────────
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


class VerifyPayload(BaseModel):
    email: str
    code: Optional[int] = None  # Resend'de code gerekmior; only verify'de zorunlu



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


# ═══════════════════════════════════════════════════════════════
# ─── Email Service (Minimal Inline) ─────────────────────────
# ═══════════════════════════════════════════════════════════════

# Aktif provider: console | resend | smtp

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "mkemal@pythonmulakat.com")


def _send_email(to: str, subject: str, html: str, text: str) -> bool:
        try:
            # ✅ Native HTTP — resend SDK dependency yok
            import requests as http_requests  # 'requests' paketi zaten FastAPI bagimliligi

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
    """Verification email — inline HTML, dark gradient, minimal."""
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
<h2 style="margin:0 0 8px;color:#fafafa;font-size:20px;font-weight:700;">Hoş geldin, {username}! 👋</h2>
<p style="margin:0 0 32px;color:#a1a1aa;font-size:15px;line-height:1.6;">Hesabını aktive etmek için aşağıdaki kodu kullan.</p>
<div style="background:linear-gradient(135deg,rgba(251,191,36,0.08) 0%,rgba(99,102,241,0.08) 100%);border:1.5px dashed rgba(251,191,36,0.5);border-radius:14px;padding:32px 16px;text-align:center;margin:0 0 32px;">
<p style="margin:0 0 12px;color:#a1a1aa;font-size:11px;letter-spacing:2.5px;text-transform:uppercase;font-weight:700;">Doğrulama Kodun</p>
<div style="font-family:'SF Mono',Menlo,monospace;font-size:44px;font-weight:800;color:#fbbf24;letter-spacing:10px;line-height:1;margin:8px 0;">{code}</div>
<p style="margin:16px 0 0;color:#71717a;font-size:12px;">⏰ {expires_minutes} dakika geçerli</p>
</div>
<table role="presentation" width="100%"><tr><td align="center" style="padding:0 0 32px;">
<a href="https://www.pythonmulakat.com/login" style="display:inline-block;background:linear-gradient(135deg,#fbbf24 0%,#f59e0b 100%);color:#0a0a0f;text-decoration:none;font-weight:700;font-size:15px;padding:16px 36px;border-radius:12px;">Kodu Gir ve Giriş Yap →</a>
</td></tr></table>
</td></tr>
<tr><td style="background:rgba(0,0,0,0.4);padding:18px 32px;text-align:center;border-top:1px solid rgba(255,255,255,0.04);">
<p style="margin:0;color:#52525b;font-size:11px;">© 2026 PythonMulakat · Tüm hakları saklıdır.</p>
</td></tr>
</table>
</td></tr></table>
</body></html>"""


def _verification_email_text(username: str, code: str, expires_minutes: int = 15) -> str:
    """Plain-text fallback."""
    return f"""Merhaba {username},

PythonMulakat'a hoş geldin!

Doğrulama kodun: {code}

Bu kod {expires_minutes} dakika geçerlidir.

Eğer bu kayıt isteğini sen yapmadıysan, bu emaili görmezden gelebilirsin.

—
PythonMulakat Ekibi
"""


# ═══════════════════════════════════════════════════════════════
# ─── Helpers ────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

def _generate_6_digit_code() -> int:
    return secrets.randbelow(900000) + 100000


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
# ─── Router ──────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse)
async def register(payload: RegisterPayload):
    """Register — kullanıcı oluştur, profile yaz, kod üret, email gönder."""
    try:
        if not payload.privacy_policy_consent:
            raise HTTPException(400, "Gizlilik politikası kabul edilmedi")

        sb_admin = get_supabase_admin()

        # 1. User oluştur
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
            if "already" in error_msg or "exists" in error_msg:
                raise HTTPException(409, "Bu e-posta zaten kayıtlı")
            raise HTTPException(400, f"Kayıt hatası: {str(e)}")

        # 2. Profile oluştur
        _ensure_profile(sb_admin, user_id, payload.email, payload.username)

        # 3. Verification code üret + DB'ye yaz
        code = _generate_6_digit_code()
        expires_at = (datetime.datetime.utcnow() + datetime.timedelta(minutes=15)).isoformat()
        sb_admin.table("profiles").update({
            "verification_code": str(code),
            "verification_code_expires_at": expires_at,
        }).eq("id", user_id).execute()

        # 4. ✅ EMAIL GÖNDER
        html = _verification_email_html(payload.username, str(code))
        text = _verification_email_text(payload.username, str(code))
        _send_email(
            to=payload.email,
            subject=f"🐍 PythonMulakat — Doğrulama Kodun: {code}",
            html=html,
            text=text,
        )

        logger.info(f"📧 Registered: {payload.email} → code: {code}")

        return MessageResponse(
            ok=True,
            message=f"Kayıt başarılı. Doğrulama kodu: {code}",
            verified=False,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Register endpoint error")
        raise HTTPException(500, f"Kayıt hatası: {str(e)}")


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginPayload):
    """Login — Supabase session döndür."""
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
            raise HTTPException(401, f"Giriş hatası: {str(e)}")

        # Profile bilgisi
        profile = None
        try:
            result = sb_admin.table("profiles").select("*").eq("id", user.id).maybe_single().execute()
            profile = result.data
        except Exception as e:
            logger.warning(f"Profile fetch error: {e}")

        return _build_auth_response(session, profile)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Login endpoint error")
        raise HTTPException(500, f"Giriş hatası: {str(e)}")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(payload: VerifyPayload):
    """Email doğrulama kodu kontrolü."""
    try:
        sb_admin = get_supabase_admin()

        result = sb_admin.table("profiles").select("*").eq("email", payload.email).maybe_single().execute()

        if not result.data:
            raise HTTPException(404, "Kullanıcı bulunamadı")

        profile = result.data
        stored_code = str(profile.get("verification_code", ""))

        if not stored_code:
            raise HTTPException(400, "Doğrulama kodu bulunamadı. Yeni kod talep edin.")
        if stored_code != str(payload.code):
            raise HTTPException(400, "Geçersiz doğrulama kodu")

        # Expiration
        expires_str = profile.get("verification_code_expires_at", "")
        if expires_str:
            try:
                expires = datetime.datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                if datetime.datetime.now(datetime.timezone.utc) > expires:
                    raise HTTPException(400, "Kodun süresi dolmuş")
            except (ValueError, TypeError):
                pass

        # Verification başarılı
        sb_admin.table("profiles").update({
            "is_verified": True,
            "verification_code": None,
            "verification_code_expires_at": None,
        }).eq("id", profile["id"]).execute()

        logger.info(f"✅ Email verified: {payload.email}")

        return MessageResponse(
            ok=True,
            message="E-posta doğrulandı. Giriş yapabilirsiniz.",
            verified=True,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Verify endpoint error")
        raise HTTPException(500, f"Doğrulama hatası: {str(e)}")


@router.post("/resend-code", response_model=MessageResponse)
async def resend_code(payload: VerifyPayload):
    """Yeni doğrulama kodu gönder (email ile)."""
    try:
        sb_admin = get_supabase_admin()

        result = sb_admin.table("profiles").select("id, username, email").eq("email", payload.email).maybe_single().execute()
        if not result.data:
            raise HTTPException(404, "Kullanıcı bulunamadı")

        profile = result.data
        new_code = _generate_6_digit_code()
        expires_at = (datetime.datetime.utcnow() + datetime.timedelta(minutes=15)).isoformat()

        sb_admin.table("profiles").update({
            "verification_code": str(new_code),
            "verification_code_expires_at": expires_at,
        }).eq("id", profile["id"]).execute()

        # ✅ EMAIL GÖNDER
        username = profile.get("username", payload.email.split("@")[0])
        html = _verification_email_html(username, str(new_code))
        text = _verification_email_text(username, str(new_code))
        _send_email(
            to=payload.email,
            subject=f"🐍 PythonMulakat — Yeni Doğrulama Kodun: {new_code}",
            html=html,
            text=text,
        )

        logger.info(f"📧 Resent code to {payload.email}: {new_code}")

        return MessageResponse(
            ok=True,
            message=f"Yeni kod email'e gönderildi: {new_code}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Resend endpoint error")
        raise HTTPException(500, f"Kod gönderilemedi: {str(e)}")


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
            result = sb_admin.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
            profile = result.data
        except Exception:
            pass

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
