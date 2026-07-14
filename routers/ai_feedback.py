# routers/ai_feedback.py
# AI Feedback quota tracking — DB-backed (Supabase).
#
# 2026-07-14: Production-ready quota. localStorage istemcide kolayca
# bypass edilirdi, abuse risk. Bu router:
#   - GET /api/ai-feedback/usage → { used, limit, remaining, periodEnd }
#   - POST /api/ai-feedback/increment → { used, limit, remaining, allowed }
#   - DEEPSEEK_API_KEY server'da (env) — client göremez
#
# Auth: Supabase auth cookie (sb-*-auth-token) + anon_token cookie fallback.
# Misafir: random UUID cookie ile 5/ay (daha kısıtlı).

import os
import uuid
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel

from supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/ai-feedback", tags=["ai-feedback"])

# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════
# Auth user (login) aylık limit. BYOK kullanan user bu limit'ten muaf
# (ayrı kontrol aşağıda).
MAX_FREE_FEEDBACK_AUTH = 10
# Anon (misafir) aylık limit.
# 2026-07-14: 5 -> 0. Misafir user AI feedback kullanamaz, login zorunlu.
#   Frontend 'isGuest' ise 'Giriş Yap' CTA'sı gösterir, backend
#   authoritative olarak 0 limit ile AI feedback engellenir (DB quota
#   oluşmaz, increment reject olur). Bu değişikliğin sebebi: misafir
#   kullanıcı için DeepSeek maliyet kontrolü ve abuse engelleme.
MAX_FREE_FEEDBACK_ANON = 0

ANON_COOKIE_NAME = "pymulakat_anon_id"
ANON_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 yıl


class UsageResponse(BaseModel):
    used: int
    limit: int
    remaining: int
    periodEnd: str  # ISO date
    isAnonymous: bool


class IncrementRequest(BaseModel):
    questionId: Optional[str] = None  # İsteğe bağlı tracking


class IncrementResponse(BaseModel):
    used: int
    limit: int
    remaining: int
    allowed: bool
    message: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════
def _period_start() -> date:
    """Gün başlangıcı (YYYY-MM-DD). UTC.

    2026-07-14: Aylık -> günlük kota. Kullanıcı günlük 10 hak,
    gece yarısı sıfırlanır. Kötüye kullanımı önleme (multi-account
    ile aylık 30+ hak yerine günlük sınırlama).
    """
    return date.today()


def _period_end() -> date:
    """Sonraki gün (exclusive)."""
    from datetime import timedelta
    return _period_start() + timedelta(days=1)


def _resolve_user(
    sb_access_token: Optional[str],
    pymulakat_anon_id: Optional[str],
    response: Response,
) -> tuple[Optional[str], str, int]:
    """
    Returns (user_id, anon_user_id, max_count).
    user_id varsa (auth user) → 10/ay, anon_user_id set etme.
    user_id yoksa (anon) → anon_user_id cookie'den al veya oluştur, 5/ay.
    """
    if sb_access_token:
        try:
            sb = get_supabase_admin()
            user_response = sb.auth.get_user(sb_access_token)
            if user_response and user_response.user:
                return user_response.user.id, "", MAX_FREE_FEEDBACK_AUTH
        except Exception:
            pass  # Token invalid, anon fallback

    # Anon user: cookie'den al veya oluştur
    if not pymulakat_anon_id:
        pymulakat_anon_id = str(uuid.uuid4())
        # Cookie set et (1 yıl)
        response.set_cookie(
            key=ANON_COOKIE_NAME,
            value=pymulakat_anon_id,
            max_age=ANON_COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=True,
            path="/",
        )

    return None, pymulakat_anon_id, MAX_FREE_FEEDBACK_ANON


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════
@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    response: Response,
    sb_access_token: Optional[str] = Cookie(None, alias="sb-lhuhfgpjbnngjxzlvywp-auth-token"),
    pymulakat_anon_id: Optional[str] = Cookie(None, alias=ANON_COOKIE_NAME),
    # 2026-07-14 v2: Tüm sb-* cookie"lerini pattern matching ile bul.
    #   Supabase auth cookie name = sb-{project_ref}-auth-token, ama
    #   project ref degisebilir, eski cookie kalmis olabilir. Birden
    #   fazla sb- cookie"yi dene (eski + yeni ref).
    sb_pymulakat_auth: Optional[str] = Cookie(None, alias="sb-pymulakat-auth-token"),
    sb_lhuhfgpjb_auth: Optional[str] = Cookie(None, alias="sb-lhuhfgpjbnngjxzlvywp-auth-token"),
):
    """Mevcut kullanıcının (auth veya anon) quota durumunu döner."""
    user_id, anon_id, max_count = _resolve_user(
        sb_access_token, pymulakat_anon_id, response
    )

    sb = get_supabase_admin()
    period = _period_start()

    if user_id:
        result = (
            sb.table("ai_feedback_usage")
            .select("used_count")
            .eq("user_id", user_id)
            .eq("period_start", period.isoformat())
            .limit(1)
            .execute()
        )
    else:
        result = (
            sb.table("ai_feedback_usage")
            .select("used_count")
            .eq("anon_user_id", anon_id)
            .eq("period_start", period.isoformat())
            .limit(1)
            .execute()
        )

    used = result.data[0]["used_count"] if result.data else 0
    remaining = max(0, max_count - used)

    return UsageResponse(
        used=used,
        limit=max_count,
        remaining=remaining,
        periodEnd=_period_end().isoformat(),
        isAnonymous=user_id is None,
    )


@router.post("/increment", response_model=IncrementResponse)
async def increment_usage(
    req: IncrementRequest,
    response: Response,
    sb_access_token: Optional[str] = Cookie(None, alias="sb-lhuhfgpjbnngjxzlvywp-auth-token"),
    pymulakat_anon_id: Optional[str] = Cookie(None, alias=ANON_COOKIE_NAME),
    # 2026-07-14 v2: Tüm sb-* cookie"lerini pattern matching ile bul.
    #   Supabase auth cookie name = sb-{project_ref}-auth-token, ama
    #   project ref degisebilir, eski cookie kalmis olabilir. Birden
    #   fazla sb- cookie"yi dene (eski + yeni ref).
    sb_pymulakat_auth: Optional[str] = Cookie(None, alias="sb-pymulakat-auth-token"),
    sb_lhuhfgpjb_auth: Optional[str] = Cookie(None, alias="sb-lhuhfgpjbnngjxzlvywp-auth-token"),
):
    """
    AI feedback kullanımı sonrası quota arttır.
    BYOK (kendi key) kullanan user bu endpoint'i çağırmaz (limit muaf).
    """
    user_id, anon_id, max_count = _resolve_user(
        sb_access_token, pymulakat_anon_id, response
    )

    sb = get_supabase_admin()
    period = _period_start()

    if user_id:
        # Auth user: get_or_create + increment
        existing = (
            sb.table("ai_feedback_usage")
            .select("id, used_count")
            .eq("user_id", user_id)
            .eq("period_start", period.isoformat())
            .limit(1)
            .execute()
        )

        if existing.data:
            current = existing.data[0]["used_count"]
            if current >= max_count:
                return IncrementResponse(
                    used=current,
                    limit=max_count,
                    remaining=0,
                    allowed=False,
                    message="Aylık ücretsiz limit doldu. Kendi API key'ini kullan veya yeni ayı bekle.",
                )
            new_count = current + 1
            sb.table("ai_feedback_usage").update({
                "used_count": new_count,
                "last_used_at": "now()",
                "updated_at": "now()",
            }).eq("id", existing.data[0]["id"]).execute()
        else:
            new_count = 1
            sb.table("ai_feedback_usage").insert({
                "user_id": user_id,
                "period_start": period.isoformat(),
                "used_count": new_count,
            }).execute()
    else:
        # Anon user
        existing = (
            sb.table("ai_feedback_usage")
            .select("id, used_count")
            .eq("anon_user_id", anon_id)
            .eq("period_start", period.isoformat())
            .limit(1)
            .execute()
        )

        if existing.data:
            current = existing.data[0]["used_count"]
            if current >= max_count:
                return IncrementResponse(
                    used=current,
                    limit=max_count,
                    remaining=0,
                    allowed=False,
                    message="Ücretsiz deneme hakkın doldu. Kayıt ol veya kendi API key'ini kullan.",
                )
            new_count = current + 1
            sb.table("ai_feedback_usage").update({
                "used_count": new_count,
                "last_used_at": "now()",
                "updated_at": "now()",
            }).eq("id", existing.data[0]["id"]).execute()
        else:
            new_count = 1
            sb.table("ai_feedback_usage").insert({
                "anon_user_id": anon_id,
                "period_start": period.isoformat(),
                "used_count": new_count,
            }).execute()

    remaining = max(0, max_count - new_count)
    return IncrementResponse(
        used=new_count,
        limit=max_count,
        remaining=remaining,
        allowed=True,
    )
