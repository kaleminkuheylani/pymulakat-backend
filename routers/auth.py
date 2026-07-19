# backend/routers/auth.py
# 2026-07-19: SADECE OAuth (Google/GitHub). Email/sifre endpoint'leri kaldirildi.
# OAuth akisi Supabase client tarafindan yurutulur; backend sadece JWT dogrulama
# (/auth/me) ve cikis stub'u saglar.

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request

from dependencies import get_current_user
from supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ═══════════════════════════════════════════════════════════════
# ─── Schemas ────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

class MessageResponse:
    ok: bool
    message: str

    def __init__(self, ok: bool, message: str):
        self.ok = ok
        self.message = message


# ═══════════════════════════════════════════════════════════════
# ─── Logout ───────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.post("/logout", response_model=MessageResponse)
async def logout():
    return MessageResponse(ok=True, message="Çıkış başarılı")


# ═══════════════════════════════════════════════════════════════
# ─── Current User ───────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

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
