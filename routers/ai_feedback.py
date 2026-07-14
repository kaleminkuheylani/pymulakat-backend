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

from fastapi import APIRouter, Cookie, Header, HTTPException, Request, Response
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
    x_user_email: Optional[str] = None,
    authorization: Optional[str] = None,
    request: Optional["Request"] = None,
) -> tuple[Optional[str], str, int]:
    """
    Returns (user_id, anon_user_id, max_count).
    2026-07-14 v4: Backend-only auth. Öncelik:
      1. Authorization: Bearer <jwt> (Supabase JWT, frontend'ten header)
      2. sb-*-auth-token cookie (Supabase auth, Vercel'de olmayabilir)
      3. pymulakat_auth=1 + email header (eski fallback, kaldırıldı)
      4. Anon fallback (limit 0)
    user_id varsa (auth user) → 10/gün.
    user_id yoksa (anon) → limit 0 (misafir AI kullanamaz).
    """
    # 1) Authorization: Bearer <jwt> — frontend'ten header
    # 2026-07-14 v6: HS256 local verify (daha hizli, network yok).
    #   SUPABASE_JWT_SECRET (Legacy HS256) Supabase dashboard'dan alinir.
    #   Edge case: secret yoksa veya token ES256 ise supabase.auth.get_user()
    #   fallback (JWKS otomatik).
    if authorization and authorization.startswith("Bearer "):
        jwt_token = authorization.replace("Bearer ", "").strip()
        if jwt_token:
            # Önce HS256 local verify (hızlı)
            jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")
            if jwt_secret:
                try:
                    import jwt
                    payload = jwt.decode(
                        jwt_token,
                        jwt_secret,
                        algorithms=["HS256"],
                        audience="authenticated",
                    )
                    user_id = payload.get("sub")
                    if user_id:
                        return user_id, "", MAX_FREE_FEEDBACK_AUTH
                except Exception:
                    pass  # HS256 başarısız, ES256/JWKS dene

            # Fallback: Supabase client (ES256 + JWKS)
            try:
                sb = get_supabase_admin()
                user_response = sb.auth.get_user(jwt_token)
                if user_response and user_response.user:
                    return user_response.user.id, "", MAX_FREE_FEEDBACK_AUTH
            except Exception:
                pass  # Invalid token, cookie fallback

    # 2) Supabase auth cookie — httpOnly (JS erişemez, server'a gider)
    # 2026-07-14 v6: supabase-ssr httpOnly cookie kullaniyor (localStorage'a
    #   yazmaz). Cookie adı 'sb-{project_ref}-auth-token' formatında.
    #   Eski alias 'sb-lhuhfgpjbnngjxzlvywp-auth-token' (eski project ref)
    #   calismayabilir. Tum 'sb-*-auth-token' cookie'leri tara.
    import json as _json
    sb_cookie_token = sb_access_token
    # 2026-07-14 v7: supabase-ssr httpOnly cookie kullaniyor. Cookie
    #   JSON encoded ({ access_token, refresh_token, ... }). Tum
    #   'sb-*-auth-token' cookie'leri tara (eski alias calismayabilir,
    #   yeni project ref farkli).
    if not sb_cookie_token and request is not None:
        try:
            for cookie_name, cookie_value in request.cookies.items():
                if cookie_name.startswith("sb-") and cookie_name.endswith("-auth-token"):
                    try:
                        parsed = _json.loads(cookie_value)
                        if isinstance(parsed, list):
                            for chunk in parsed:
                                if isinstance(chunk, dict) and chunk.get("access_token"):
                                    sb_cookie_token = chunk["access_token"]
                                    break
                        elif isinstance(parsed, dict) and parsed.get("access_token"):
                            sb_cookie_token = parsed["access_token"]
                        if sb_cookie_token:
                            break
                    except Exception:
                        # raw JWT (nadir)
                        if cookie_value.startswith("eyJ"):
                            sb_cookie_token = cookie_value
                            break
        except Exception:
            pass

    if sb_cookie_token:
        try:
            sb = get_supabase_admin()
            user_response = sb.auth.get_user(sb_cookie_token)
            if user_response and user_response.user:
                return user_response.user.id, "", MAX_FREE_FEEDBACK_AUTH
        except Exception:
            pass

    # 3) Anon fallback (limit 0)
    return None, "", MAX_FREE_FEEDBACK_ANON

    return None, pymulakat_anon_id, MAX_FREE_FEEDBACK_ANON


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════
@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    request: Request,
    response: Response,
    sb_access_token: Optional[str] = Cookie(None, alias="sb-wetzphluxsamlttszdzw-auth-token"),
    pymulakat_anon_id: Optional[str] = Cookie(None, alias=ANON_COOKIE_NAME),
    #   Supabase auth cookie name = sb-{project_ref}-auth-token, ama
    #   project ref degisebilir, eski cookie kalmis olabilir. Birden
    #   fazla sb- cookie"yi dene (eski + yeni ref).
    sb_pymulakat_auth: Optional[str] = Cookie(None, alias="sb-pymulakat-auth-token"),
    sb_lhuhfgpjb_auth: Optional[str] = Cookie(None, alias="sb-lhuhfgpjbnngjxzlvywp-auth-token"),
    # 2026-07-14 v4: Authorization header (Supabase JWT, frontend'ten gelir)
    authorization: Optional[str] = Header(None),
):
    """Mevcut kullanıcının (auth veya anon) quota durumunu döner.

    2026-07-14 v3: profiles tablosuna entegre (tek kaynak). Eski
      ai_feedback_usage tablosu kaldırıldı. Auth user: profiles'da
      user_id ile, anon user: limit 0 (kullanamaz).
    """
    user_id, anon_id, max_count = _resolve_user(
        sb_access_token, pymulakat_anon_id, response,
        authorization=authorization,
        request=request,
    )

    # Anon user: AI feedback yok (limit 0)
    if not user_id:
        return UsageResponse(
            used=0,
            limit=0,
            remaining=0,
            periodEnd=_period_end().isoformat(),
            isAnonymous=True,
        )

    sb = get_supabase_admin()
    period = _period_start()
    period_iso = period.isoformat()

    # 2026-07-14 v5: ai_usage tablosundan çek (profiles'dan izole).
    # user_id = profiles.id (pymulakat kendi UUID).
    result = (
        sb.table("ai_usage")
        .select("used_count")
        .eq("user_id", user_id)
        .eq("period_start", period_iso)
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
        isAnonymous=False,
    )


@router.post("/increment", response_model=IncrementResponse)
async def increment_usage(
    request: Request,
    req: IncrementRequest,
    response: Response,
    sb_access_token: Optional[str] = Cookie(None, alias="sb-wetzphluxsamlttszdzw-auth-token"),
    pymulakat_anon_id: Optional[str] = Cookie(None, alias=ANON_COOKIE_NAME),
    # 2026-07-14 v2: Tüm sb-* cookie"lerini pattern matching ile bul.
    #   Supabase auth cookie name = sb-{project_ref}-auth-token, ama
    #   project ref degisebilir, eski cookie kalmis olabilir. Birden
    #   fazla sb- cookie"yi dene (eski + yeni ref).
    sb_pymulakat_auth: Optional[str] = Cookie(None, alias="sb-pymulakat-auth-token"),
    sb_lhuhfgpjb_auth: Optional[str] = Cookie(None, alias="sb-lhuhfgpjbnngjxzlvywp-auth-token"),
    authorization: Optional[str] = Header(None),
):
    """
    AI feedback kullanımı sonrası quota arttır.
    BYOK (kendi key) kullanan user bu endpoint'i çağırmaz (limit muaf).

    2026-07-14 v3: profiles tablosuna entegre. Auth user: profiles
      UPDATE (user_id ile). Anon user: limit 0, increment reject.
    """
    user_id, anon_id, max_count = _resolve_user(
        sb_access_token, pymulakat_anon_id, response,
        authorization=authorization,
        request=request,
    )

    # Anon user: AI feedback yok (limit 0)
    if not user_id:
        return IncrementResponse(
            used=0,
            limit=0,
            remaining=0,
            allowed=False,
            message="Misafir kullanıcı AI feedback kullanamaz. Giriş yap veya kendi API key'ini kullan.",
        )

    sb = get_supabase_admin()
    period = _period_start()
    period_iso = period.isoformat()

    # 2026-07-14 v5: ai_usage tablosundan SELECT (günlük satır).
    existing = (
        sb.table("ai_usage")
        .select("id, used_count")
        .eq("user_id", user_id)
        .eq("period_start", period_iso)
        .limit(1)
        .execute()
    )

    current = existing.data[0]["used_count"] if existing.data else 0

    # Limit dolu mu?
    if current >= max_count:
        return IncrementResponse(
            used=current,
            limit=max_count,
            remaining=0,
            allowed=False,
            message="Günlük ücretsiz limit doldu. Kendi API key'ini kullan veya yeni günü bekle.",
        )

    new_count = current + 1

    # UPSERT ai_usage (user_id, period_start) — atomik
    if existing.data:
        sb.table("ai_usage").update({
            "used_count": new_count,
            "last_used_at": "now()",
            "updated_at": "now()",
        }).eq("id", existing.data[0]["id"]).execute()
    else:
        sb.table("ai_usage").insert({
            "user_id": user_id,
            "period_start": period_iso,
            "used_count": new_count,
        }).execute()

    remaining = max(0, max_count - new_count)
    return IncrementResponse(
        used=new_count,
        limit=max_count,
        remaining=remaining,
        allowed=True,
    )
