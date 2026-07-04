# backend/routers/play_count.py
# Kod oynatma sayacı: her setCode çağrısında debounced increment.
# Optimistic UI: client localStorage'da da tutar (offline-friendly).

from fastapi import APIRouter, Request
from dependencies import get_current_user
from supabase_client import get_supabase_admin
import logging

router = APIRouter(prefix="/api/v2/users", tags=["users-v2"])
logger = logging.getLogger(__name__)


@router.post("/me/play-count")
async def increment_play_count(request: Request):
    """Kullanıcının toplam kod oynatma sayısını 1 artır.

    Frontend her setCode çağrısında bu endpoint'i çağırır (debounced).
    DB'de profiles.play_count kolonu tutulur.
    """
    try:
        user = await get_current_user(request)
        if not user or not user.get("id"):
            return {"ok": False, "reason": "unauthenticated"}

        user_id = user["id"]
        sb = get_supabase_admin()

        # Önce mevcut değeri oku (PostgREST'te increment yok, ya da yok)
        try:
            current = (
                sb.table("profiles")
                .select("play_count")
                .eq("id", user_id)
                .maybe_single()
                .execute()
            )
            current_value = (current.data or {}).get("play_count") or 0
            new_value = int(current_value) + 1
        except Exception:
            new_value = 1  # İlk kez oynatıyorsa

        # Update
        sb.table("profiles").update({"play_count": new_value}).eq("id", user_id).execute()

        return {"ok": True, "play_count": new_value}
    except Exception as e:
        logger.warning("play_count.increment.failed err=%s", e)
        return {"ok": False, "reason": str(e)}


@router.get("/me/play-count")
async def get_play_count(request: Request):
    """Kullanıcının mevcut play_count değerini döndür."""
    try:
        user = await get_current_user(request)
        if not user or not user.get("id"):
            return {"ok": False, "play_count": 0}

        user_id = user["id"]
        sb = get_supabase_admin()

        result = (
            sb.table("profiles")
            .select("play_count")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        play_count = (result.data or {}).get("play_count") or 0
        return {"ok": True, "play_count": int(play_count)}
    except Exception as e:
        logger.warning("play_count.get.failed err=%s", e)
        return {"ok": False, "play_count": 0, "reason": str(e)}