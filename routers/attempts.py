# backend/routers/attempts.py — DEBUG VERSION

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from supabase import Client
from dependencies import get_current_user
from supabase_client import get_supabase, get_supabase_admin
from question_loader import get_question

router = APIRouter(prefix="/api/v2/attempts", tags=["attempts-v2"])


class AttemptOut(BaseModel):
    id: str
    user_id: str
    question_id: int
    question_title: Optional[str] = None
    category: Optional[str] = None
    passed_tests: int
    total_tests: int
    success: bool
    execution_time_ms: int
    hints_used: int
    created_at: str
    user_code: Optional[str] = None


class AttemptsListResponse(BaseModel):
    data: List[AttemptOut]
    total: int


class AttemptStatsResponse(BaseModel):
    total_attempts: int
    success_count: int
    fail_count: int
    success_rate: int
    points: int
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
        print(f"📝 [ATTEMPT] user_id={user_id}, payload={payload}")

        # ✅ SERVICE_ROLE kullan (RLS bypass)
        sb = get_supabase_admin()

        attempt_data = {
            "user_id": user_id,
            "question_id": int(payload.get("question_id", 0)),
            "passed_tests": int(payload.get("passed_tests", 0)),
            "total_tests": int(payload.get("total_tests", 0)),
            "success": bool(payload.get("success", False)),
            "execution_time_ms": int(payload.get("execution_time_ms", 0)),
            "hints_used": int(payload.get("hints_used", 0)),
            "user_code": str(payload.get("user_code", "")),
        }

        print(f"💾 [ATTEMPT] Saving: {attempt_data}")

        result = sb.table("interview_attempts").insert(attempt_data).execute()

        if not result.data:
            print(f"❌ [ATTEMPT] Insert returned no data")
            raise HTTPException(500, "Attempt kaydedilemedi")

        print(f"✅ [ATTEMPT] Saved with id={result.data[0].get('id')}")
        return {"ok": True, "id": str(result.data[0].get("id"))}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [ATTEMPT] Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Attempt hatası: {str(e)}")


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
        print(f"📋 [LIST] user_id={user_id}, limit={limit}")

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
        print(f"📊 [LIST] Found {len(rows)} rows for user {user_id}")

        items = []
        for r in rows:
            q = get_question(r.get("question_id"))
            items.append({
                "id": str(r.get("id", "")),
                "user_id": r.get("user_id", user_id),
                "question_id": r.get("question_id"),
                "question_title": q.title if q else f"Soru #{r.get('question_id')}",
                "category": q.category if q else None,
                "passed_tests": r.get("passed_tests", 0),
                "total_tests": r.get("total_tests", 0),
                "success": r.get("success", False),
                "execution_time_ms": r.get("execution_time_ms", 0),
                "hints_used": r.get("hints_used", 0),
                "created_at": r.get("created_at", ""),
                "user_code": r.get("user_code"),
            })

        return AttemptsListResponse(data=items, total=len(items))
    except Exception as e:
        print(f"❌ [LIST] Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
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
        points = sum(a.get("passed_tests", 0) * 10 for a in attempts if a.get("success"))
        avg_time_ms = (
            sum(a.get("execution_time_ms", 0) for a in attempts) / total if total else 0
        )

        return AttemptStatsResponse(
            total_attempts=total,
            success_count=success,
            fail_count=fail,
            success_rate=round((success / total * 100) if total else 0),
            points=points,
            solution_average_time=int(avg_time_ms / 1000),
            solution_average_time_ms=int(avg_time_ms),
        )
    except Exception as e:
        print(f"❌ [STATS] Error: {str(e)}")
        return AttemptStatsResponse(
            total_attempts=0, success_count=0, fail_count=0,
            success_rate=0, points=0, solution_average_time=0,
            solution_average_time_ms=0,
        )
