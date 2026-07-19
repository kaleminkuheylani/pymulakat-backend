# backend/routers/attempts.py
# Production logs temizlendi — kullanıcı kodu/verisi artık print()'lenmiyor.
# Hata logları için Python logging modülü kullanılıyor (INFO+DEBUG varsayılan kapalı).

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from supabase import Client
from dependencies import get_current_user
from supabase_client import get_supabase, get_supabase_admin
from question_loader import get_question

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/attempts", tags=["attempts-v2"])


class AttemptOut(BaseModel):
    id: str
    user_id: str
    question_id: int
    question_title: Optional[str] = None
    question_slug: Optional[str] = None
    question_category: Optional[str] = None
    is_orphaned: bool = False  # Eski interviews'tan gelen, yeni questions tablosunda olmayan
    category: Optional[str] = None
    passed_tests: int
    total_tests: int
    success: bool
    execution_time_ms: int
    hints_used: int
    created_at: str
    # 📌 user_code KVKK uyumu icin DB'de tutulmuyor.
    # Kod sadece kullanici tarayicisinda calistirilir, server'a gonderilmez.


class AttemptsListResponse(BaseModel):
    data: List[AttemptOut]
    total: int


class AttemptStatsResponse(BaseModel):
    total_attempts: int
    success_count: int
    fail_count: int
    success_rate: int
    points: int
    attempt_points: int = 0
    achievement_points: int = 0
    solution_average_time: int
    solution_average_time_ms: int


# ═══════════════════════════════════════════════════════════════
# ─── POST /api/v2/attempts (frontend → backend) ──────────────
# ═══════════════════════════════════════════════════════════════

@router.post("")
async def create_attempt(
    request: Request,
    payload: Dict[str, Any],
):
    """Yeni attempt kaydet — DEBUG LOG'LU."""
    try:
        # ✅ Manuel user decode (Depends yerine)
        from dependencies import get_current_user
        user = await get_current_user(request)

        if not user or not user.get("id"):
            raise HTTPException(401, "User bulunamadı")

        user_id = user["id"]
        # 📌 user_code KVKK uyumu icin kaydedilmiyor.
        # Sandbox zaten client-side (Pyodide), kod hic server'a gelmiyor.
        raw_qid = payload.get("question_id")
        try:
            question_id = int(raw_qid or 0)
        except (TypeError, ValueError):
            question_id = 0
        if question_id <= 0:
            raise HTTPException(400, "question_id gerekli ve > 0 olmali")

        # ✅ question_id public (legacy_id) olabilir; interview_attempts FK questions.id'ye
        # giderse gercek row id'yi bul.
        sb = get_supabase_admin()
        real_qid = question_id
        try:
            q_res = (
                sb.table("questions")
                .select("id, legacy_id")
                .or_(f"id.eq.{question_id},legacy_id.eq.{question_id}")
                .limit(1)
                .execute()
            )
            if q_res.data:
                real_qid = q_res.data[0].get("id") or question_id
            else:
                logger.warning("attempt.question_not_found user=%s q=%s", user_id, question_id)
        except Exception as q_err:
            logger.warning("attempt.question_lookup_failed user=%s q=%s err=%s", user_id, question_id, q_err)

        logger.info(
            "attempt.create user=%s q=%s real_q=%s passed=%s/%s success=%s",
            user_id,
            question_id,
            real_qid,
            payload.get("passed_tests"),
            payload.get("total_tests"),
            payload.get("success"),
        )

        attempt_data = {
            "user_id": user_id,
            "question_id": real_qid,
            "passed_tests": int(payload.get("passed_tests", 0) or 0),
            "total_tests": int(payload.get("total_tests", 0) or 0),
            "success": bool(payload.get("success", False)),
            "execution_time_ms": int(payload.get("execution_time_ms", 0) or 0),
            "hints_used": int(payload.get("hints_used", 0) or 0),
            # 2026-07-15: Hangi dilde denendi (python/javascript/rust) - istatistik + filtering
            "language": str(payload.get("language", "python") or "python").lower()[:20],
            # 📌 user_code KALDIRILDI — sadece stats kaydedilir
        }

        # Eger language kolonu migration calistirilmamis olursa fallback
        try:
            result = sb.table("interview_attempts").insert(attempt_data).execute()
        except Exception as insert_err:
            err_msg = str(insert_err).lower()
            if "language" in err_msg or "column" in err_msg or "does not exist" in err_msg:
                logger.warning("attempt.language_fallback user=%s q=%s err=%s", user_id, question_id, insert_err)
                del attempt_data["language"]
                result = sb.table("interview_attempts").insert(attempt_data).execute()
            else:
                raise

        if not result.data:
            logger.error("attempt.insert.empty user=%s q=%s", user_id, question_id)
            raise HTTPException(500, "Attempt kaydedilemedi")

        logger.info("attempt.saved user=%s id=%s q=%s", user_id, result.data[0].get("id"), question_id)
        return {"ok": True, "id": str(result.data[0].get("id"))}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("attempt.create failed: %s", e)
        detail = f"Attempt kaydedilemedi: {e}"
        raise HTTPException(500, detail[:500])


# ═══════════════════════════════════════════════════════════════
# ─── GET /api/v2/attempts?limit=10 ──────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("", response_model=AttemptsListResponse)
async def list_my_attempts(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
):
    """Kullanıcının son N attempt'i — DEBUG LOG'LU."""
    try:
        from dependencies import get_current_user
        user = await get_current_user(request)

        if not user or not user.get("id"):
            return AttemptsListResponse(data=[], total=0)

        user_id = user["id"]
        logger.debug("attempts.list user=%s limit=%s", user_id, limit)

        # ✅ SERVICE_ROLE kullan (RLS bypass)
        sb = get_supabase_admin()

        result = (
            sb.table("interview_attempts")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        rows = result.data or []
        logger.debug("attempts.list.count user=%s count=%s", user_id, len(rows))

        items = []
        for r in rows:
            q = get_question(r.get("question_id"))
            qid = r.get("question_id")
            # Orphans (DB'den gelmedi, QUESTIONS-v3'te yok) → placeholder
            if q:
                title = q.title
                category = q.category
                slug = getattr(q, "slug", None) or None
                is_orphaned = False
            else:
                title = f"Silinmis soru (ID: {qid})"
                category = None
                slug = None
                is_orphaned = True

            items.append({
                "id": str(r.get("id", "")),
                "user_id": r.get("user_id", user_id),
                "question_id": qid,
                "question_title": title,
                "question_slug": slug,
                "question_category": category,
                "is_orphaned": is_orphaned,
                "category": category,
                "passed_tests": r.get("passed_tests", 0),
                "total_tests": r.get("total_tests", 0),
                "success": r.get("success", False),
                "execution_time_ms": r.get("execution_time_ms", 0),
                "hints_used": r.get("hints_used", 0),
                "created_at": r.get("created_at", ""),
                # 📌 user_code response'tan kaldirildi
            })

        return AttemptsListResponse(data=items, total=len(items))
    except Exception as e:
        logger.exception("attempts.list.failed user=%s", user_id)
        return AttemptsListResponse(data=[], total=0)


# ═══════════════════════════════════════════════════════════════
# ─── GET /api/v2/attempts/stats ────────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("/stats", response_model=AttemptStatsResponse)
async def my_stats(
    request: Request,
):
    """Kullanıcı istatistikleri — DEBUG LOG'LU."""
    try:
        from dependencies import get_current_user
        user = await get_current_user(request)

        if not user or not user.get("id"):
            return AttemptStatsResponse(
                total_attempts=0, success_count=0, fail_count=0,
                success_rate=0, points=0, solution_average_time=0,
                solution_average_time_ms=0,
            )

        user_id = user["id"]
        sb = get_supabase_admin()

        result = (
            sb.table("interview_attempts")
            .select("passed_tests, total_tests, success, execution_time_ms")
            .eq("user_id", user_id)
            .execute()
        )

        attempts = result.data or []
        total = len(attempts)
        success = sum(1 for a in attempts if a.get("success"))
        fail = total - success
        attempt_points = sum(a.get("passed_tests", 0) * 10 for a in attempts if a.get("success"))
        avg_time_ms = (
            sum(a.get("execution_time_ms", 0) for a in attempts) / total if total else 0
        )

        achievement_points = 0
        try:
            achievement_points = sum(
                r.get("points", 0) or 0
                for r in (sb.table("user_achievements").select("points").eq("user_id", user_id).execute().data or [])
            )
        except Exception as e:
            logger.warning("attempts.stats.achievements.fetch_failed user=%s err=%s", user_id, e)

        return AttemptStatsResponse(
            total_attempts=total,
            success_count=success,
            fail_count=fail,
            success_rate=round((success / total * 100) if total else 0),
            points=attempt_points + achievement_points,
            attempt_points=attempt_points,
            achievement_points=achievement_points,
            solution_average_time=int(avg_time_ms / 1000),
            solution_average_time_ms=int(avg_time_ms),
        )
    except Exception as e:
        logger.exception("attempts.stats.failed user=%s", user_id)
        return AttemptStatsResponse(
            total_attempts=0, success_count=0, fail_count=0,
            success_rate=0, points=0, solution_average_time=0,
            solution_average_time_ms=0,
        )


# ═══════════════════════════════════════════════════════════════
# Solved question IDs — QuestionTable için
# ═══════════════════════════════════════════════════════════════

class SolvedListResponse(BaseModel):
    solved: List[int] = []  # Tam çözülmüş sorular (success=true)
    attempted: List[int] = []  # Denenmiş ama tam çözülmemiş


@router.get("/solved-batch", response_model=SolvedListResponse)
async def solved_batch(request: Request):
    """Kullanıcının solved + attempted question_id listesi.

    QuestionTable her soruda 'solved' badge göstermek için kullanır.
    Misafir → boş liste döner.
    """
    try:
        from dependencies import get_current_user
        user = await get_current_user(request)

        if not user or not user.get("id"):
            return SolvedListResponse(solved=[], attempted=[])

        user_id = user["id"]
        sb = get_supabase_admin()

        # success=true olan question_id'ler (solved)
        solved_res = (
            sb.table("interview_attempts")
            .select("question_id")
            .eq("user_id", user_id)
            .eq("success", True)
            .execute()
        )
        solved_ids = sorted(set(r["question_id"] for r in (solved_res.data or [])))

        # success=false olan question_id'ler (attempted, henüz çözülmedi)
        attempted_res = (
            sb.table("interview_attempts")
            .select("question_id")
            .eq("user_id", user_id)
            .eq("success", False)
            .execute()
        )
        attempted_ids = sorted(set(r["question_id"] for r in (attempted_res.data or [])))

        return SolvedListResponse(solved=solved_ids, attempted=attempted_ids)
    except Exception as e:
        logger.warning("attempts.solved_batch.failed user=%s", user_id)
        return SolvedListResponse(solved=[], attempted=[])
