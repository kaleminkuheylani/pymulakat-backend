# backend/routers/questions.py
# /api/v2/questions — İSKELET (4 endpoint)
#
# Tüm soru verisi DB'den (question_loader üzerinden).
# Kod içinde veri yok, dosya fallback yok.

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from supabase import Client

from question_loader import filter_questions, get_question, get_question_by_slug
from dependencies import get_current_user
from supabase_client import get_supabase

logger = logging.getLogger(__name__)
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
    test_cases: list[dict] = Field(default_factory=list)
    function_name: Optional[str] = None
    hints: list[str] = Field(default_factory=list)
    explanation: Optional[str] = None
    complexity: Optional[str] = None
    related_concepts: list[str] = Field(default_factory=list)
    related_question_ids: list[int] = Field(default_factory=list)
    tutorial_slug: Optional[str] = None
    slug: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: list[str] = Field(default_factory=list)


class TestsResponse(BaseModel):
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


class QuestionsListResponse(BaseModel):
    data: list[QuestionOut]
    meta: PaginationMeta


class AllQuestionsResponse(BaseModel):
    data: list[QuestionOut]
    total: int


# ═══════════════════════════════════════════════════════════════
# ─── Helpers ──────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

def _q_get(q, key, default=None):
    """Hem dataclass hem dict için güvenli erişim."""
    if q is None:
        return default
    if isinstance(q, dict):
        return q.get(key, default)
    return getattr(q, key, default)


def _extract_function_name(starter_code: Optional[str]) -> str:
    if not starter_code:
        return "solution"
    for line in starter_code.splitlines():
        line = line.strip()
        if line.startswith("def "):
            return line.split("(")[0].replace("def ", "").strip()
    return "solution"


def _to_jsonb_list(v):
    """PostgREST JSONB alanı bazen string döndürür. Güvenli list dönüşümü."""
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return []


def _to_question_out(q, include_starter: bool = False) -> QuestionOut:
    raw_test_cases = _to_jsonb_list(_q_get(q, "test_cases", []))
    test_cases = raw_test_cases
    starter_code = _q_get(q, "starter_code") if include_starter else None
    function_name = (
        _extract_function_name(starter_code)
        if include_starter and starter_code
        else _q_get(q, "function_name") or None
    )
    return QuestionOut(
        id=_q_get(q, "id"),
        title=_q_get(q, "title", ""),
        description=_q_get(q, "description", "") or "",
        level=_q_get(q, "level"),
        topic=_q_get(q, "topic"),
        category=_q_get(q, "category"),
        tags=_to_jsonb_list(_q_get(q, "tags", [])),
        starter_code=starter_code,
        test_count=len(test_cases),
        test_cases=test_cases if include_starter else [],
        function_name=function_name,
        hints=_to_jsonb_list(_q_get(q, "hints", [])),
        explanation=_q_get(q, "explanation"),
        complexity=_q_get(q, "complexity"),
        related_concepts=_to_jsonb_list(_q_get(q, "related_concepts", [])),
        related_question_ids=_to_jsonb_list(_q_get(q, "related_question_ids", [])),
        tutorial_slug=_q_get(q, "tutorial_slug"),
        slug=str(_q_get(q, "slug") or _q_get(q, "id")),
        meta_title=_q_get(q, "meta_title"),
        meta_description=_q_get(q, "meta_description"),
        meta_keywords=_to_jsonb_list(_q_get(q, "meta_keywords", [])),
    )


# ═══════════════════════════════════════════════════════════════
# ─── 1. LIST — GET /api/v2/questions ─────────────────────
# ═══════════════════════════════════════════════════════════════

@router.get("", response_model=QuestionsListResponse)
def list_questions(
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    filtered = filter_questions(category=category, level=level, search=search, tag=tag)
    total = len(filtered)
    total_pages = max(1, (total + limit - 1) // limit)
    if page > total_pages and total > 0:
        raise HTTPException(400, f"Sayfa {page} mevcut değil")
    offset = (page - 1) * limit
    page_items = filtered[offset:offset + limit]
    return QuestionsListResponse(
        data=[_to_question_out(q, include_starter=False) for q in page_items],
        meta=PaginationMeta(
            page=page, limit=limit, total=total, total_pages=total_pages,
            has_next=page < total_pages, has_prev=page > 1,
        ),
    )


# ═══════════════════════════════════════════════════════════════
# ─── 2. ALL (minimal) — GET /api/v2/questions/all ─────────
# ═══════════════════════════════════════════════════════════════

@router.get("/all", response_model=AllQuestionsResponse)
def list_all_questions():
    """Slug listesi için minimal payload (canonical URL üretimi)."""
    filtered = filter_questions()
    items = [_to_question_out(q, include_starter=False) for q in filtered]
    return AllQuestionsResponse(data=items, total=len(items))


# ═══════════════════════════════════════════════════════════════
# ─── 3. DETAIL — GET /api/v2/questions/by-slug/{category}/{slug}
# ═══════════════════════════════════════════════════════════════

@router.get("/by-slug/{category}/{slug}", response_model=QuestionOut)
def get_question_by_slug_endpoint(
    category: str,
    slug: str,
    include_starter: bool = Query(True),
):
    q = get_question_by_slug(slug, category=category)
    if not q:
        raise HTTPException(404, f"{category}/{slug} bulunamadı")
    return _to_question_out(q, include_starter=include_starter)


@router.get("/by-slug/{category}/{slug}/tests", response_model=TestsResponse)
def get_question_tests_by_slug(category: str, slug: str):
    q = get_question_by_slug(slug, category=category)
    if not q:
        raise HTTPException(404, f"{category}/{slug} bulunamadı")

    starter_code = _q_get(q, "starter_code", "") or ""
    test_cases_raw = _q_get(q, "test_cases", []) or []

    safe_tests: List[Dict[str, Any]] = []
    if isinstance(test_cases_raw, list):
        for tc in test_cases_raw:
            if isinstance(tc, dict):
                safe_tests.append({
                    "input": tc.get("input"),
                    "expected": tc.get("expected"),
                    # 📌 Referans çözüm çıktısı (varsa) misafirlere önizleme olarak dönderilir.
                    #    DB'de "actual" key'i yoksa None olur — frontend "Beklenen" gibi davranır.
                    "actual": tc.get("actual"),
                    "description": tc.get("description", ""),
                })

    return TestsResponse(data={
        "question_id": _q_get(q, "id"),
        "title": _q_get(q, "title", ""),
        "function_name": _q_get(q, "function_name") or _extract_function_name(starter_code),
        "test_cases": safe_tests,
    })


# ═══════════════════════════════════════════════════════════════
# ─── 4. PROGRESS — GET /api/v2/questions/by-slug/{category}/{slug}/progress
# ═══════════════════════════════════════════════════════════════

@router.get("/by-slug/{category}/{slug}/progress", response_model=ProgressResponse)
def get_question_progress_by_slug(
    category: str,
    slug: str,
    user=Depends(get_current_user),
    sb: Client = Depends(get_supabase),
):
    q = get_question_by_slug(slug, category=category)
    if not q:
        raise HTTPException(404, f"{category}/{slug} bulunamadı")
    question_id = q.id

    try:
        result = (
            sb.table("interview_attempts")
            .select("passed_tests,total_tests,success,execution_time_ms,hints_used,created_at")
            .eq("user_id", user["id"])
            .eq("question_id", question_id)
            .order("success", desc=True)
            .limit(1)
            .execute()
        )
        total_attempts = (
            sb.table("interview_attempts")
            .select("id", count="exact")
            .eq("user_id", user["id"])
            .eq("question_id", question_id)
            .execute()
        ).count or 0
        best = result.data[0] if result.data else None
        return ProgressResponse(data={
            "question_id": question_id,
            "best_attempt": best,
            "total_attempts": total_attempts,
        })
    except Exception as e:
        logger.warning("progress.failed user=%s q=%s: %s", user.get("id") if user else None, question_id, e)
        return ProgressResponse(data={"question_id": question_id, "best_attempt": None, "total_attempts": 0})


# ═══════════════════════════════════════════════════════════════
# ─── Legacy ID fallback — GET /api/v2/questions/{id} ──────
# ═══════════════════════════════════════════════════════════════

@router.get("/{question_id}", response_model=QuestionOut)
def get_question_detail(question_id: int, include_starter: bool = Query(True)):
    q = get_question(question_id)
    if not q:
        raise HTTPException(404, f"Soru #{question_id} bulunamadı")
    return _to_question_out(q, include_starter=include_starter)


@router.get("/{question_id}/tests", response_model=TestsResponse)
def get_question_tests_by_id(question_id: int):
    """Sorunun test case'lerini ID ile getir (public — auth gerekmez).

    WorkspaceClient bu endpoint'i kullanır; /by-slug/{cat}/{slug}/tests ile aynı formatta.
    """
    q = get_question(question_id)
    if not q:
        raise HTTPException(404, f"Soru #{question_id} bulunamadı")

    starter_code = _q_get(q, "starter_code", "") or ""
    test_cases_raw = _q_get(q, "test_cases", []) or []

    safe_tests: List[Dict[str, Any]] = []
    if isinstance(test_cases_raw, list):
        for tc in test_cases_raw:
            if isinstance(tc, dict):
                safe_tests.append({
                    "input": tc.get("input"),
                    "expected": tc.get("expected"),
                    "actual": tc.get("actual"),
                    "description": tc.get("description", ""),
                })

    return TestsResponse(data={
        "question_id": _q_get(q, "id"),
        "title": _q_get(q, "title", ""),
        "function_name": _q_get(q, "function_name") or _extract_function_name(starter_code),
        "test_cases": safe_tests,
    })