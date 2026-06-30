# backend/routers/questions.py
# /api/v2/questions — RESTful, envelope, RFC uyumlu pagination

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from supabase import Client
from question_loader import filter_questions, get_question
from dependencies import get_current_user
from supabase_client import get_supabase

router = APIRouter(prefix="/interviews/v1", tags=["interviews-v1"])


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


class TestCaseOut(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    input: List[Any]
    expected: Any
    description: Optional[str] = None


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
# ─── HELPERS — Question dataclass / dict dual-handling ─────
# ═══════════════════════════════════════════════════════════════

def _q_get(q: Any, key: str, default: Any = None) -> Any:
    """Question dataclass veya dict'ten değer al."""
    if isinstance(q, dict):
        return q.get(key, default)
    return getattr(q, key, default)


def _to_question_out(q: Any, include_starter: bool = False) -> QuestionOut:
    """Question objesini (dataclass veya dict) QuestionOut'a çevir."""
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


def _extract_function_name(starter_code: str) -> str:
    """Starter code'dan fonksiyon adını çıkarır."""
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

@router.get(
    "",
    response_model=QuestionsListResponse,
    responses={400: {"description": "Geçersiz sayfa"}},
)
def list_questions(
    category: Optional[str] = Query(None, description="Kategori slug (örn: python-basics)"),
    level: Optional[str] = Query(None, description="Zorluk: beginner/intermediate/advanced veya başlangıç/orta/ileri"),
    search: Optional[str] = Query(None, description="Başlık/açıklamada arama"),
    tag: Optional[str] = Query(None, description="Etiket filtresi"),
    page: int = Query(1, ge=1, description="Sayfa numarası (1-based)"),
    limit: int = Query(20, ge=1, le=500, description="Sayfa başına kayıt (max 500)"),
):
    """
    Soruları listele — filtreleme + RFC uyumlu pagination.

    Örnekler:
      GET /api/v2/questions
      GET /api/v2/questions?category=python-basics&level=beginner
      GET /api/v2/questions?search=palindrome&page=2&limit=10
      GET /api/v2/questions?tag=string
    """
    all_filtered = filter_questions(
        category=category,
        level=level,
        search=search,
        tag=tag,
    )

    total = len(all_filtered)
    total_pages = max(1, (total + limit - 1) // limit)

    if page > total_pages and total > 0:
        raise HTTPException(400, f"Sayfa {page} mevcut değil. Toplam sayfa: {total_pages}")

    offset = (page - 1) * limit
    page_items = all_filtered[offset : offset + limit]

    items = [_to_question_out(q, include_starter=False) for q in page_items]

    return QuestionsListResponse(
        data=items,
        meta=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            next_page=page + 1 if page < total_pages else None,
            prev_page=page - 1 if page > 1 else None,
        ),
    )


# ═══════════════════════════════════════════════════════════════
# ─── ALL — GET /api/v2/questions/all ─────────────────────
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/all",
    response_model=AllQuestionsResponse,
    summary="Tüm soruları pagination olmadan getir",
)
def list_all_questions(
    category: Optional[str] = Query(None, description="Kategori slug"),
    level: Optional[str] = Query(None, description="Zorluk seviyesi"),
    search: Optional[str] = Query(None, description="Arama terimi"),
    include_starter: bool = Query(False, description="Starter code dahil et"),
):
    """Tüm soruları pagination olmadan tek seferde döner (maks. 500)."""
    all_filtered = filter_questions(
        category=category,
        level=level,
        search=search,
    )
    items = all_filtered[:500]
    return AllQuestionsResponse(
        data=[_to_question_out(q, include_starter=include_starter) for q in items],
        total=len(items),
    )


# ═══════════════════════════════════════════════════════════════
# ─── DETAIL — GET /api/v2/questions/{id} ───────────────────
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/{question_id}",
    response_model=QuestionOut,
    responses={404: {"description": "Soru bulunamadı"}},
)
def get_question_detail(
    question_id: int,
    include_starter: bool = Query(False, description="Starter code dahil et"),
):
    """Tek soru detayı — sadece ID."""
    q = get_question(question_id)
    if not q:
        raise HTTPException(404, f"Soru #{question_id} bulunamadı")

    return _to_question_out(q, include_starter=include_starter)


# ═══════════════════════════════════════════════════════════════
# ─── TESTS — GET /api/v2/questions/{id}/tests ──────────────
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/{question_id}/tests",
    response_model=QuestionTestsResponse,
    responses={
        404: {"description": "Soru bulunamadı"},
        401: {"description": "Auth gerekli"},
    },
)
def get_question_tests(
    question_id: int,
    user=Depends(get_current_user),
):
    """Soruya ait test case'ler — auth zorunlu."""
    q = get_question(question_id)
    if not q:
        raise HTTPException(404, f"Soru #{question_id} bulunamadı")

    starter_code = _q_get(q, "starter_code", "")
    test_cases = _q_get(q, "test_cases", []) or []

    return QuestionTestsResponse(
        data={
            "question_id": _q_get(q, "id"),
            "title": _q_get(q, "title", ""),
            "function_name": _extract_function_name(starter_code),
            "test_cases": test_cases,
        }
    )


# ═══════════════════════════════════════════════════════════════
# ─── PROGRESS — GET /api/v2/questions/{id}/progress ────────
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/{question_id}/progress",
    response_model=ProgressResponse,
    responses={
        404: {"description": "Soru bulunamadı"},
        401: {"description": "Auth gerekli"},
    },
)
def get_question_progress(
    question_id: int,
    user=Depends(get_current_user),
    sb: Client = Depends(get_supabase),
):
    """Kullanıcının belirli sorudaki en iyi denemesi — auth zorunlu."""
    try:
        result = (
            sb.table("interview_attempts")
            .select("passed_tests, total_tests, success, execution_time_ms, hints_used, created_at")
            .eq("user_id", user["id"])
            .eq("question_id", question_id)
            .order("success", desc=True)
            .order("passed_tests", desc=True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data:
            return ProgressResponse(
                data={
                    "question_id": question_id,
                    "best_attempt": None,
                    "total_attempts": 0,
                }
            )

        total_attempts = (
            sb.table("interview_attempts")
            .select("id", count="exact")
            .eq("user_id", user["id"])
            .eq("question_id", question_id)
            .execute()
        ).count

        return ProgressResponse(
            data={
                "question_id": question_id,
                "best_attempt": result.data[0],
                "total_attempts": total_attempts or 0,
            }
        )
    except Exception as e:
        # Supabase tablosu yoksa veya hata varsa, boş döndür
        print(f"⚠️ Progress sorgu hatası: {e}")
        return ProgressResponse(
            data={
                "question_id": question_id,
                "best_attempt": None,
                "total_attempts": 0,
            }
        )