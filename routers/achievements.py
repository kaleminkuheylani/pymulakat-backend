# routers/achievements.py
# Kullanıcı achievements listesi + otomatik değerlendirme.

import logging
from typing import List, Dict, Any, Set
from fastapi import APIRouter, HTTPException, Request
from dependencies import get_current_user
from supabase_client import get_supabase_admin
from services.achievements import evaluate, get_achievements_with_state, ACHIEVEMENTS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/achievements", tags=["achievements"])


def _to_date_key(iso_str: str) -> str:
    try:
        from datetime import datetime
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00").replace("+00:00", "")).strftime("%Y-%m-%d")
    except Exception:
        return iso_str[:10] if isinstance(iso_str, str) else ""


@router.get("")
async def list_achievements(request: Request):
    user = await get_current_user(request)
    if not user or not user.get("id"):
        raise HTTPException(401, "Token gerekli")
    user_id = user["id"]
    sb = get_supabase_admin()

    try:
        attempts_res = (
            sb.table("interview_attempts")
            .select("question_id, passed_tests, total_tests, success, execution_time_ms, hints_used, language, created_at")
            .eq("user_id", user_id)
            .execute()
        )
        attempts = attempts_res.data or []
    except Exception as e:
        logger.exception("achievements.attempts.fetch_failed user=%s", user_id)
        raise HTTPException(500, f"Denemeler alınamadı: {e}")

    try:
        questions_res = (
            sb.table("questions")
            .select("id, category, level")
            .execute()
        )
        questions = questions_res.data or []
    except Exception as e:
        logger.warning("achievements.questions.fetch_failed user=%s err=%s", user_id, e)
        questions = []

    unlocked = evaluate(attempts, questions)

    try:
        share_res = (
            sb.table("forms")
            .select("id")
            .eq("user_id", user_id)
            .eq("category", "share")
            .limit(1)
            .execute()
        )
        if share_res.data:
            unlocked.append("share_first")
    except Exception as e:
        logger.warning("achievements.forms.fetch_failed user=%s err=%s", user_id, e)

    try:
        report_res = (
            sb.table("question_reports")
            .select("id")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if report_res.data:
            unlocked.append("report_question")
    except Exception as e:
        logger.warning("achievements.reports.fetch_failed user=%s err=%s", user_id, e)

    try:
        ai_res = (
            sb.table("ai_usage")
            .select("used_count")
            .eq("user_id", user_id)
            .execute()
        )
        ai_total = sum(r.get("used_count", 0) for r in (ai_res.data or []))
        if ai_total >= 5:
            unlocked.append("ai_feedback_5")
    except Exception as e:
        logger.warning("achievements.ai_usage.fetch_failed user=%s err=%s", user_id, e)

    unlocked_set: Set[str] = set(unlocked)

    try:
        existing_res = (
            sb.table("user_achievements")
            .select("achievement_id")
            .eq("user_id", user_id)
            .execute()
        )
        existing_ids = {r["achievement_id"] for r in (existing_res.data or [])}
    except Exception as e:
        logger.error("achievements.user_achievements.fetch_failed user=%s err=%s", user_id, e)
        existing_ids = set()
        # Devam et; sadece okunur hata

    new_ids = unlocked_set - existing_ids
    if new_ids:
        id_to_points = {a.id: a.points for a in ACHIEVEMENTS}
        insert_rows = [
            {"user_id": user_id, "achievement_id": aid, "points": id_to_points.get(aid, 0)}
            for aid in new_ids
        ]
        try:
            sb.table("user_achievements").insert(insert_rows).execute()
        except Exception as e:
            logger.exception("achievements.insert_failed user=%s new=%s err=%s", user_id, new_ids, e)
            # Yeni kilitli açılmamış kabul et, listeyi yine de dön
            unlocked_set = existing_ids
            new_ids = set()

    total_points = sum(a.points for a in ACHIEVEMENTS if a.id in unlocked_set)
    items = get_achievements_with_state(unlocked_set)

    new_unlocked = [
        {"id": a.id, "title": a.title, "points": a.points}
        for a in ACHIEVEMENTS
        if a.id in new_ids
    ]

    groups: Dict[str, List[Dict[str, Any]]] = {}
    for it in items:
        groups.setdefault(it["group"], []).append(it)

    return {
        "items": items,
        "groups": groups,
        "new_unlocked": new_unlocked,
        "unlocked_count": len(unlocked_set),
        "total": len(ACHIEVEMENTS),
        "achievement_points": total_points,
    }
