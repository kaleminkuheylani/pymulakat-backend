# routers/coach.py
# Email koç servisi — admin endpoint'leri + dry-run

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from supabase import Client

from services.coach import (
    recommend_for_user,
    send_recommendation,
    load_user_activity,
    load_all_active_users,
)
from dependencies import get_current_user
from supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/coach", tags=["coach"])


class RecommendationOut(BaseModel):
    rule: str
    subject: str
    user_email: str


class RecommendationsResponse(BaseModel):
    user_id: str
    recommendations: List[RecommendationOut]


class SendResult(BaseModel):
    user_id: str
    sent: int
    failed: int
    errors: List[str] = []


# ═══════════════════════════════════════════════════════════
# GET /api/v2/coach/recommendations/:user_id
# Dry-run: kuralları değerlendir, mail göndermeden listele.
# ═══════════════════════════════════════════════════════════
@router.get("/recommendations/{user_id}", response_model=RecommendationsResponse)
async def get_recommendations(
    user_id: str,
    request,
):
    """Bir kullanıcı için hangi maillerin tetikleneceğini döndür (dry-run)."""
    try:
        await get_current_user(request)
    except Exception:
        pass  # dev ortamı için opsiyonel

    recs = recommend_for_user(user_id, dry_run=True)
    return RecommendationsResponse(
        user_id=user_id,
        recommendations=[
            RecommendationOut(
                rule=r["rule"],
                subject=r["email"]["subject"],
                user_email=r["user"]["email"],
            )
            for r in recs
        ],
    )


# ═══════════════════════════════════════════════════════════
# POST /api/v2/coach/send/:user_id
# Bir kullanıcı için kuralları değerlendir + uygun mailleri gönder.
# ═══════════════════════════════════════════════════════════
@router.post("/send/{user_id}", response_model=SendResult)
async def send_for_user(
    user_id: str,
    request,
    force: bool = Query(False, description="Frequency cap'i bypass et"),
):
    """Bir kullanıcıya coach mail(ler)i gönder."""
    try:
        await get_current_user(request)
    except Exception:
        pass

    recs = recommend_for_user(user_id, dry_run=not force)
    sent = 0
    failed = 0
    errors = []
    for rec in recs:
        if send_recommendation(rec):
            sent += 1
        else:
            failed += 1
            errors.append(rec["rule"])
    return SendResult(user_id=user_id, sent=sent, failed=failed, errors=errors)


# ═══════════════════════════════════════════════════════════
# POST /api/v2/coach/send-all
# Tüm aktif kullanıcılara coach mail gönder (cron tarafından çağrılır).
# ═══════════════════════════════════════════════════════════
@router.post("/send-all", response_model=List[SendResult])
async def send_all(
    request,
    days_window: int = Query(30, ge=1, le=90),
    force: bool = Query(False),
):
    """Aktif kullanıcılara coach mailleri gönder. Admin / cron endpoint'i."""
    try:
        await get_current_user(request)
    except Exception:
        pass

    users = load_all_active_users(days_window=days_window)
    results = []
    for u in users:
        uid = u.get("id")
        if not uid:
            continue
        recs = recommend_for_user(uid, dry_run=not force)
        sent = 0
        failed = 0
        errors = []
        for rec in recs:
            if send_recommendation(rec):
                sent += 1
            else:
                failed += 1
                errors.append(rec["rule"])
        results.append(SendResult(user_id=uid, sent=sent, failed=failed, errors=errors))
    return results


# ═══════════════════════════════════════════════════════════
# GET /api/v2/coach/stats/:user_id
# Bir kullanıcının coach istatistikleri (debug için).
# ═══════════════════════════════════════════════════════════
@router.get("/stats/{user_id}")
async def get_stats(user_id: str):
    """Kullanıcının attempt özeti (debug)."""
    act = load_user_activity(user_id)
    if not act:
        raise HTTPException(404, "User bulunamadı")
    return {
        "user_id": act.user_id,
        "email": act.email,
        "username": act.username,
        "points": act.points,
        "total_solved": act.total_solved,
        "total_attempted": act.total_attempted,
        "failed_count": len(act.failed_ids),
        "days_since_active": act.days_since_active,
        "last_active": act.last_active.isoformat() if act.last_active else None,
        "solved_ids": act.solved_ids[:20],
    }