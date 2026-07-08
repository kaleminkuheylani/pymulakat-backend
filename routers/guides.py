# routers/guides.py
# Etüt (study guide) endpoint'leri — zor sorular için detaylı analiz.
# CSV kaynağı: data/guide-v4.csv (sonra Supabase question_studies tablosuna taşınacak)

import csv
from pathlib import Path
from typing import Optional, Dict, List, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from question_loader import get_question_by_slug, get_question

router = APIRouter(prefix="/api/v2/guides", tags=["guides-v1"])

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class Approach(BaseModel):
    title: str
    complexity: Optional[str] = None
    code: Optional[str] = None


class StudyGuide(BaseModel):
    question_id: int
    study_slug: str
    seo_title: str
    category: str
    level: str
    keywords: List[str]
    meta_description: str
    estimated_read_time_min: int
    prereq_topics: str
    difficulty_progression: str
    related_question_ids: List[int]
    # İçerik (henüz yok — sonra Supabase'den)
    problem_understanding: Optional[str] = None
    approach_1: Optional[Approach] = None
    approach_2: Optional[Approach] = None
    approach_3: Optional[Approach] = None
    challenges: Optional[str] = None


# ─── Guide cache (CSV'den yükle) ────────────────────────────────
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
                "study_slug": row.get("study_slug", ""),
                "seo_title": row.get("seo_title", ""),
                "category": row.get("category", ""),
                "level": row.get("level", ""),
                "keywords": [k.strip() for k in row.get("keywords", "").split(",") if k.strip()],
                "meta_description": row.get("meta_description", ""),
                "estimated_read_time_min": int(row.get("estimated_read_time_min", 8) or 8),
                "prereq_topics": row.get("prereq_topics", ""),
                "difficulty_progression": row.get("difficulty_progression", ""),
                "related_question_ids": [
                    int(x) for x in row.get("related_question_ids", "").split(",") if x.strip().isdigit()
                ],
            }
    _GUIDE_CACHE = cache
    return cache


# ─── Endpoint: by question_id ────────────────────────────────
@router.get("/by-question-id/{question_id}", response_model=StudyGuide)
def get_guide_by_question_id(question_id: int):
    guides = _load_guides_csv()
    if question_id not in guides:
        raise HTTPException(404, f"Bu soru için etüt yok (id={question_id})")
    
    g = dict(guides[question_id])
    # İçerik alanları sonra DB'den gelecek — şimdilik None
    return StudyGuide(**g)


# ─── Endpoint: by slug ────────────────────────────────────────
@router.get("/by-slug/{study_slug}", response_model=StudyGuide)
def get_guide_by_slug(study_slug: str):
    guides = _load_guides_csv()
    for qid, g in guides.items():
        if g["study_slug"] == study_slug:
            return StudyGuide(**dict(g))
    raise HTTPException(404, f"Etüt bulunamadı: {study_slug}")


# ─── Endpoint: by category (cross-link için) ───────────────────
@router.get("/by-category/{category}", response_model=List[StudyGuide])
def list_guides_by_category(category: str):
    guides = _load_guides_csv()
    results = [StudyGuide(**dict(g)) for qid, g in guides.items() if g["category"] == category]
    return sorted(results, key=lambda x: x.question_id)


# ─── Endpoint: sitemap için ───────────────────────────────────
@router.get("/all", response_model=List[StudyGuide])
def list_all_guides():
    guides = _load_guides_csv()
    return [StudyGuide(**dict(g)) for qid, g in sorted(guides.items())]


def invalidate_cache():
    global _GUIDE_CACHE
    _GUIDE_CACHE = {}
