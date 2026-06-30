# backend/routers/questions.py
# /api/v2/questions — RESTful, envelope, RFC uyumlu pagination
# FIXED VERSION — test_cases güvenli normalize

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from supabase import Client
from question_loader import filter_questions, get_question
from dependencies import get_current_user
from supabase_client import get_supabase

router = APIRouter(prefix="/api/v2/questions", tags=["questions-v2"])


# ═══════════════════════════════════════════════════════════════
# ─── Schemas ──────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

class QuestionOut(BaseModel):
    id: int
    title: str
    description: str = ""
    level: Optional[str] = None
    topic: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    starter_code: Optional[str] = None
    test_count: int = 0


class QuestionTestsResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    data: Dict[str, Any]


class ProgressResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    data: Dict[str, Any]


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None


class QuestionsListResponse(BaseModel):
    data: list[QuestionOut]
    meta: PaginationMeta


class AllQuestionsResponse(BaseModel):
    data: list[QuestionOut]
    total: int


# ═══════════════════════════════════════════════════════════════
# ─── Helpers — dataclass / dict dual-handling ─────────────
# ═══════════════════════════════════════════════════════════════

def _q_get(q, key, default=None):
    """Hem dict hem dataclass için güvenli erişim."""
    if q is None:
        return default
    if isinstance(q, dict):
        return q.get(key, default)
    return getattr(q, key, default)


def _to_question_out(q, include_starter=False):
    test_cases = _q_get(q, "test_cases", []) or []
    if not isinstance(test_cases, list):
        test_cases = []
    return QuestionOut(
        id=_q_get(q, "id"),
        title=_q_get(q, "title", ""),
        description=_q_get(q, "description", "") or "",
        level=_q_get(q, "level"),
        topic=_q_get(q, "topic"),
        category=_q_get(q, "category"),
        tags=_q_get(q, "tags", []) or [],
        starter_code=_q_get(q, "starter_code") if include_starter else None,
        test_count=len(test_cases),
    )


def _extract_function_name(starter_code):
    if not starter_code:
        return "solution"
    for line in starter_code.splitlines():
        line = line.strip()
        if line.startswith("def "):
            return line.split("(")[0].replace("def ", "").strip()
    return "solution"


# ═══════════════════════════════════════════════════════════════
# ─── LIST — GET /api/v2/questions ──────────────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("", response_model=QuestionsListResponse, responses={400: {"description": "Geçersiz sayfa"}})
def list_questions(
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=500),
):
    all_filtered = filter_questions(category=category, level=level, search=search, tag=tag)
    total = len(all_filtered)
    total_pages = max(1, (total + limit - 1) // limit)
    if page > total_pages and total > 0:
        raise HTTPException(400, f"Sayfa {page} mevcut değil.")
    offset = (page - 1) * limit
    page_items = all_filtered[offset:offset + limit]
    items = [_to_question_out(q, include_starter=False) for q in page_items]
    return QuestionsListResponse(
        data=items,
        meta=PaginationMeta(
            page=page, limit=limit, total=total, total_pages=total_pages,
            has_next=page < total_pages, has_prev=page > 1,
            next_page=page + 1 if page < total_pages else None,
            prev_page=page - 1 if page > 1 else None,
        ),
    )


# ═══════════════════════════════════════════════════════════════
# ─── ALL — GET /api/v2/questions/all ─────────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("/all", response_model=AllQuestionsResponse)
def list_all_questions(
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    include_starter: bool = Query(False),
):
    all_filtered = filter_questions(category=category, level=level, search=search)
    items = all_filtered[:500]
    return AllQuestionsResponse(
        data=[_to_question_out(q, include_starter=include_starter) for q in items],
        total=len(items),
    )


# ═══════════════════════════════════════════════════════════════
# ─── DETAIL — GET /api/v2/questions/{id} ───────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("/{question_id}", response_model=QuestionOut, responses={404: {"description": "Soru bulunamadı"}})
def get_question_detail(question_id: int, include_starter: bool = Query(False)):
    q = get_question(question_id)
    if not q:
        raise HTTPException(404, f"Soru #{question_id} bulunamadı")
    return _to_question_out(q, include_starter=include_starter)


# ═══════════════════════════════════════════════════════════════
# ─── TESTS — GET /api/v2/questions/{id}/tests ─────────────
# ═══════════════════════════════════════════════════════════════

@router.get("/{question_id}/tests", response_model=QuestionTestsResponse)
def get_question_tests(question_id: int, user=Depends(get_current_user)):
    q = get_question(question_id)
    if not q:
        raise HTTPException(404, f"Soru #{question_id} bulunamadı")

    starter_code = _q_get(q, "starter_code", "") or ""
    test_cases_raw = _q_get(q, "test_cases", []) or []

    # ✅ Güvenli normalize — her test case'i dict'e çevir
    safe_tests: List[Dict[str, Any]] = []
    if isinstance(test_cases_raw, list):
        for tc in test_cases_raw:
            if isinstance(tc, dict):
                safe_tests.append({
                    "input": tc.get("input"),
                    "expected": tc.get("expected"),
                    "description": tc.get("description", ""),
                })
            else:
                # Beklenmedik tip — string/object — olduğu gibi geçir
                safe_tests.append({"input": tc, "expected": None})

    function_name = _extract_function_name(starter_code) if starter_code else "solution"

    return QuestionTestsResponse(data={
        "question_id": _q_get(q, "id"),
        "title": _q_get(q, "title", ""),
        "function_name": function_name,
        "test_cases": safe_tests,
    })


# ═══════════════════════════════════════════════════════════════
# ─── PROGRESS — GET /api/v2/questions/{id}/progress ───────
# ═══════════════════════════════════════════════════════════════

@router.get("/{question_id}/progress", response_model=ProgressResponse)
def get_question_progress(
    question_id: int,
    user=Depends(get_current_user),
    sb: Client = Depends(get_supabase),
):
    try:
        result = (
            sb.table("interview_attempts")
            .select("passed_tests, total_tests, success, execution_time_ms, hints_used, created_at")
            .eq("user_id", user["id"])
            .eq("question_id", question_id)
            .order("success", desc=True)
            .limit(1)
            .execute()
        )
        if not result.data:
            return ProgressResponse(data={"question_id": question_id, "best_attempt": None, "total_attempts": 0})
        total_attempts = (
            sb.table("interview_attempts")
            .select("id", count="exact")
            .eq("user_id", user["id"])
            .eq("question_id", question_id)
            .execute()
        ).count or 0
        return ProgressResponse(data={"question_id": question_id, "best_attempt": result.data[0], "total_attempts": total_attempts})
    except Exception as e:
        print(f"⚠️ Progress error: {e}")
        return ProgressResponse(data={"question_id": question_id, "best_attempt": None, "total_attempts": 0})
