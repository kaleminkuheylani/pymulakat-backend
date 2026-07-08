# routers/guides.py
# Etüt (study guide) endpoint'leri.
#
# Veri akışı (öncelik sırasıyla):
#   1) DB (Supabase question_studies) — analiz DB'de varsa render et
#   2) CSV (data/guide-v4.csv) — metadata fallback (henüz analiz yoksa)
#   3) 404 — ikisinde de yoksa
#
# Neden DB > CSV:
#   - DB'de content (problem_understanding + 3 yaklaşım + challenges) zengin
#   - CSV'de yalnızca metadata var
#   - User isteği: "sadece analiz varsa render et, CSV'den değil DB'den"

import csv
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from question_loader import get_question_by_slug, get_question

router = APIRouter(prefix="/api/v2/guides", tags=["guides-v1"])
log = logging.getLogger("guides")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ─── Pydantic models ────────────────────────────────────────────

class Approach(BaseModel):
    title: str
    complexity: Optional[str] = None
    code: Optional[str] = None


class StudyGuide(BaseModel):
    question_id: int
    study_slug: Optional[str] = None
    seo_title: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    keywords: List[str] = []
    meta_description: Optional[str] = None
    estimated_read_time_min: int = 8
    prereq_topics: Optional[str] = None
    difficulty_progression: Optional[str] = None
    related_question_ids: List[int] = []
    # İçerik (DB'den gelir, yoksa None)
    problem_understanding: Optional[str] = None
    approach_1: Optional[Approach] = None
    approach_2: Optional[Approach] = None
    approach_3: Optional[Approach] = None
    challenges: Optional[str] = None
    # Debug / meta
    source: Optional[str] = None  # "db" | "csv" | "none"


# ─── CSV cache (metadata fallback) ─────────────────────────────

_GUIDE_CACHE: Dict[int, dict] = {}

def _load_guides_csv() -> Dict[int, dict]:
    """guide-v4.csv'den tüm guide metadata'yı yükle, question_id ile indexle."""
    global _GUIDE_CACHE
    if _GUIDE_CACHE:
        return _GUIDE_CACHE
    
    csv_path = DATA_DIR / "guide-v4.csv"
    if not csv_path.exists():
        return {}
    
    cache: Dict[int, dict] = {}
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                qid = int(row["question_id"])
            except (ValueError, KeyError):
                continue
            cache[qid] = {
                "question_id": qid,
                "study_slug": row.get("study_slug") or "",
                "seo_title": row.get("seo_title") or "",
                "category": row.get("category") or "",
                "level": row.get("level") or "intermediate",
                "keywords": [k.strip() for k in row.get("keywords", "").split(",") if k.strip()],
                "meta_description": row.get("meta_description") or "",
                "estimated_read_time_min": int(row.get("estimated_read_time_min", 8) or 8),
                "prereq_topics": row.get("prereq_topics") or "",
                "difficulty_progression": row.get("difficulty_progression") or "",
                "related_question_ids": [
                    int(x) for x in row.get("related_question_ids", "").split(",") if x.strip().isdigit()
                ],
            }
    _GUIDE_CACHE = cache
    return cache


def _csv_guide_to_response(g: dict) -> StudyGuide:
    """CSV dict → StudyGuide (içerik alanları None)."""
    return StudyGuide(
        question_id=g["question_id"],
        study_slug=g.get("study_slug") or None,
        seo_title=g.get("seo_title") or None,
        category=g.get("category") or None,
        level=g.get("level") or None,
        keywords=g.get("keywords", []),
        meta_description=g.get("meta_description") or None,
        estimated_read_time_min=g.get("estimated_read_time_min", 8),
        prereq_topics=g.get("prereq_topics") or None,
        difficulty_progression=g.get("difficulty_progression") or None,
        related_question_ids=g.get("related_question_ids", []),
        problem_understanding=None,
        approach_1=None,
        approach_2=None,
        approach_3=None,
        challenges=None,
        source="csv",
    )


# ─── DB query (Supabase) ───────────────────────────────────────

def _get_sb_admin():
    """Supabase service role client — RLS bypass. None ise DB kapalı."""
    try:
        from supabase_client import get_supabase_admin
        return get_supabase_admin()
    except Exception as e:
        log.warning(f"Supabase admin client alınamadı: {e}")
        return None


def _query_db_by_question_id(question_id: int) -> Optional[dict]:
    """DB'den tek satır getir. None ise bulunamadı veya DB kapalı."""
    sb = _get_sb_admin()
    if sb is None:
        return None
    try:
        r = sb.table("question_studies").select("*").eq("question_id", question_id).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        log.warning(f"DB query hata (qid={question_id}): {e}")
        return None


def _query_db_by_slug(study_slug: str) -> Optional[dict]:
    sb = _get_sb_admin()
    if sb is None:
        return None
    try:
        r = sb.table("question_studies").select("*").eq("study_slug", study_slug).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        log.warning(f"DB query hata (slug={study_slug}): {e}")
        return None


def _query_db_by_category(category: str) -> List[dict]:
    sb = _get_sb_admin()
    if sb is None:
        return []
    try:
        r = sb.table("question_studies").select("*").eq("category", category).order("question_id").execute()
        return r.data or []
    except Exception as e:
        log.warning(f"DB query hata (cat={category}): {e}")
        return []


def _query_db_all() -> List[dict]:
    sb = _get_sb_admin()
    if sb is None:
        return []
    try:
        r = sb.table("question_studies").select("*").order("question_id").execute()
        return r.data or []
    except Exception as e:
        log.warning(f"DB query hata (all): {e}")
        return []


def _db_row_to_study(row: dict) -> StudyGuide:
    """DB satırı → StudyGuide. Yaklaşım alanlarını birleştir."""
    def _approach(idx: int) -> Optional[Approach]:
        title = row.get(f"approach_{idx}_title")
        code = row.get(f"approach_{idx}_code")
        complexity = row.get(f"approach_{idx}_complexity")
        if not title and not code:
            return None
        return Approach(title=title or "", code=code, complexity=complexity)

    return StudyGuide(
        question_id=int(row["question_id"]),
        study_slug=row.get("study_slug"),
        seo_title=row.get("seo_title"),
        category=row.get("category"),
        level=row.get("level"),
        keywords=row.get("keywords") or [],
        meta_description=row.get("seo_description"),
        estimated_read_time_min=int(row.get("estimated_read_time_min") or 8),
        prereq_topics=row.get("prereq_topics"),
        difficulty_progression=row.get("difficulty_progression"),
        related_question_ids=row.get("related_question_ids") or [],
        problem_understanding=row.get("problem_understanding"),
        approach_1=_approach(1),
        approach_2=_approach(2),
        approach_3=_approach(3),
        challenges=row.get("challenges"),
        source="db",
    )


# ─── Endpoint: by question_id ──────────────────────────────────

@router.get("/by-question-id/{question_id}", response_model=StudyGuide)
def get_guide_by_question_id(question_id: int):
    """DB önce, CSV fallback."""
    # 1) DB
    row = _query_db_by_question_id(question_id)
    if row:
        return _db_row_to_study(row)
    
    # 2) CSV (metadata fallback)
    guides = _load_guides_csv()
    if question_id in guides:
        return _csv_guide_to_response(guides[question_id])
    
    raise HTTPException(404, f"Bu soru için etüt yok (id={question_id})")


# ─── Endpoint: by slug ────────────────────────────────────────

@router.get("/by-slug/{study_slug}", response_model=StudyGuide)
def get_guide_by_slug(study_slug: str):
    # 1) DB
    row = _query_db_by_slug(study_slug)
    if row:
        return _db_row_to_study(row)
    
    # 2) CSV
    guides = _load_guides_csv()
    for g in guides.values():
        if g.get("study_slug") == study_slug:
            return _csv_guide_to_response(g)
    
    raise HTTPException(404, f"Etüt bulunamadı: {study_slug}")


# ─── Endpoint: by category ─────────────────────────────────────

@router.get("/by-category/{category}", response_model=List[StudyGuide])
def list_guides_by_category(category: str):
    # 1) DB
    rows = _query_db_by_category(category)
    if rows:
        return [_db_row_to_study(r) for r in rows]
    
    # 2) CSV fallback
    guides = _load_guides_csv()
    results = [
        _csv_guide_to_response(g)
        for g in guides.values()
        if g.get("category") == category
    ]
    return sorted(results, key=lambda x: x.question_id)


# ─── Endpoint: all ────────────────────────────────────────────

@router.get("/all", response_model=List[StudyGuide])
def list_all_guides():
    # 1) DB
    rows = _query_db_all()
    if rows:
        return [_db_row_to_study(r) for r in rows]
    
    # 2) CSV fallback
    guides = _load_guides_csv()
    return [
        _csv_guide_to_response(g)
        for _, g in sorted(guides.items())
    ]


def invalidate_cache():
    global _GUIDE_CACHE
    _GUIDE_CACHE = {}
