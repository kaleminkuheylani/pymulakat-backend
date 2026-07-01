# routers/dashboard.py
# Kişisel dashboard endpoint'leri — SADECE auth'lu kullanıcı kendi verisini görür.
# Tüm query'ler user_id ile scope'lu.

import logging
from fastapi import APIRouter, HTTPException, Request, Depends

from services.reports import (
    get_user_dashboard_data, upsert_reports_from_attempts, cleanup_expired_reports,
)
from services.coach import load_user_activity
from services.skills import SKILL_GRAPH
from dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/dashboard", tags=["dashboard"])


async def _auth_user(request: Request):
    """Auth kontrol — yoksa 401."""
    try:
        user = await get_current_user(request)
    except Exception:
        raise HTTPException(401, "Giriş gerekli")
    if not user:
        raise HTTPException(401, "Giriş gerekli")
    return user


@router.get("/me")
async def get_dashboard(request: Request):
    """Ana dashboard — kullanıcının tüm kişisel verisi (auth gerekli, user scoped)."""
    user = await _auth_user(request)
    user_id = user["id"]

    try:
        data = get_user_dashboard_data(user_id)
    except Exception as e:
        logger.exception("dashboard.fetch failed user=%s", user_id)
        raise HTTPException(500, "Dashboard yüklenemedi")

    # Kullanıcı bilgisi + skill graph metadata
    act = load_user_activity(user_id)
    user_meta = {
        "id": user_id,
        "username": act.username if act else user.get("email", "").split("@")[0],
        "total_solved": act.total_solved if act else 0,
        "total_attempted": act.total_attempted if act else 0,
        "streak_days": act.streak_days if act else 0,
    }

    # Skill graph (full): tüm kategori/topic/subskill yapısı
    skill_tree = []
    for cat, topics in SKILL_GRAPH.items():
        topics_list = []
        for topic, subs in topics.items():
            topics_list.append({
                "id": f"{cat}.{topic}",
                "name": topic,
                "subskills": [{"id": f"{cat}.{topic}.{s}", "name": s} for s in subs],
            })
        skill_tree.append({
            "id": cat,
            "name": cat,
            "topics": topics_list,
        })

    return {
        "user": user_meta,
        "skill_tree": skill_tree,
        **data,
    }


@router.post("/refresh")
async def refresh_reports(request: Request):
    """Dashboard'u tazele — yeni attempt'lerden report oluştur."""
    user = await _auth_user(request)
    count = upsert_reports_from_attempts(user["id"], days=7)
    return {"new_reports": count}


@router.post("/admin/cleanup")
async def admin_cleanup(request: Request):
    """Admin-only — süresi dolmuş report'ları sil."""
    user = await _auth_user(request)
    if not user.get("is_admin"):
        raise HTTPException(403, "Admin yetkisi gerekli")
    deleted = cleanup_expired_reports()
    return {"deleted": deleted}