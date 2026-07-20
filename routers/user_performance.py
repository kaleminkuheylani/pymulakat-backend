# backend/routers/user_performance.py
# Kullanıcı toplam kullanım süresi + günlük streak takibi.

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from dependencies import get_current_user
from supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/users", tags=["users-v2"])


class SessionPayload(BaseModel):
    seconds: int = Field(..., ge=0, le=86400, description="Oturumda geçirilen saniye")


class PerformanceOut(BaseModel):
    ok: bool
    total_usage_seconds: int
    streak_count: int
    last_active_date: Optional[str]


def _today_utc() -> date:
    return datetime.now(timezone.utc).date()


def _parse_date(value) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    return None


def _compute_streak(current_streak: int, last_active: Optional[date], today: date) -> int:
    if last_active is None:
        return 1
    diff = (today - last_active).days
    if diff < 0:
        return max(current_streak, 1)
    if diff == 0:
        return max(current_streak, 1)
    if diff == 1:
        return max(current_streak, 0) + 1
    return 1


@router.post("/me/session")
async def track_session(request: Request, payload: SessionPayload):
    """Kullanıcının toplam kullanım süresine saniye ekle ve streak güncelle."""
    try:
        user = await get_current_user(request)
        if not user or not user.get("id"):
            return {"ok": False, "reason": "unauthenticated"}

        user_id = user["id"]
        seconds = payload.seconds
        today = _today_utc()
        sb = get_supabase_admin()

        existing = (
            sb.table("user_performance")
            .select("total_usage_seconds, streak_count, last_active_date")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )

        row = existing.data
        if row:
            total = (row.get("total_usage_seconds") or 0) + seconds
            current_streak = row.get("streak_count") or 0
            last_active = _parse_date(row.get("last_active_date"))
            streak = _compute_streak(current_streak, last_active, today)

            sb.table("user_performance").update({
                "total_usage_seconds": total,
                "streak_count": streak,
                "last_active_date": today.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("user_id", user_id).execute()
        else:
            total = seconds
            streak = 1
            sb.table("user_performance").insert({
                "user_id": user_id,
                "total_usage_seconds": total,
                "streak_count": streak,
                "last_active_date": today.isoformat(),
            }).execute()

        return {
            "ok": True,
            "total_usage_seconds": total,
            "streak_count": streak,
            "last_active_date": today.isoformat(),
        }
    except Exception as e:
        logger.warning("user_performance.session.failed err=%s", e)
        return {"ok": False, "reason": str(e)}


@router.get("/me/performance", response_model=PerformanceOut)
async def get_performance(request: Request):
    """Kullanıcının toplam kullanım süresi ve streak değerlerini döndür."""
    try:
        user = await get_current_user(request)
        if not user or not user.get("id"):
            return PerformanceOut(
                ok=True,
                total_usage_seconds=0,
                streak_count=0,
                last_active_date=None,
            )

        user_id = user["id"]
        sb = get_supabase_admin()

        result = (
            sb.table("user_performance")
            .select("total_usage_seconds, streak_count, last_active_date")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )

        row = result.data or {}
        return PerformanceOut(
            ok=True,
            total_usage_seconds=row.get("total_usage_seconds") or 0,
            streak_count=row.get("streak_count") or 0,
            last_active_date=str(row.get("last_active_date")) if row.get("last_active_date") else None,
        )
    except Exception as e:
        logger.warning("user_performance.get.failed err=%s", e)
        return PerformanceOut(
            ok=True,
            total_usage_seconds=0,
            streak_count=0,
            last_active_date=None,
        )
