"""
Onboarding Survey — Kullanici memnuniyet anketi.

2026-07-18: Yeni endpoint. Authenticated user ilk login sonrasi 3 soruluk
anket gosterilir. Kullanici 'Atla' veya 'Gonder' basarsa dismissed = true
isaretlenir, bir daha gosterilmez.

3 soru:
  Q1: source — Bizi nereden buldunuz? (google, reddit, youtube, x, linkedin, friend, other)
  Q2: rating — Nasil buldunuz? (great, good, meh, questions_weak, platform_useless, learning_insufficient)
  Q3: age_range — Yas araligi (15_18, 18_25, 25_35, 35_plus)

Akis:
  1. Frontend mount: GET /api/v2/survey/status
     - 401: user authenticated degil, modal gosterme
     - { dismissed: false }: modal goster
     - { dismissed: true }: gosterme
  2. User 'Gonder' basar: POST /api/v2/survey
     - dismissed = true
     - INSERT veya UPDATE
  3. User 'Atla' basar: POST /api/v2/survey { dismissed: true }
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import logging

from dependencies import get_current_user
from supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/survey", tags=["survey"])


# ─── Pydantic Models ─────────────────────────────────────

# Source: Bizi nereden buldunuz?
VALID_SOURCES = {
    "google", "reddit", "youtube", "x_twitter",
    "linkedin", "friend", "other", "skip",
}

# Rating: Nasil buldunuz? (5 secenek — 1 pozitif + 4 negatif arguman)
VALID_RATINGS = {
    "great",                              # Cok guzel
    "good",                               # Yeterli
    "questions_weak",                     # Sorular yetersiz
    "platform_useless",                   # Platform amacsiz duruyor
    "learning_insufficient",              # Programlama ogrenmek icin yetersiz
    "skip",
}

# Yas araligi
VALID_AGE_RANGES = {
    "15_18", "18_25", "25_35", "35_plus", "skip",
}


class SurveySubmit(BaseModel):
    source: Optional[str] = Field(None, description="google, reddit, youtube, x_twitter, linkedin, friend, other, skip")
    rating: Optional[str] = Field(None, description="great, good, questions_weak, platform_useless, learning_insufficient, skip")
    age_range: Optional[str] = Field(None, description="15_18, 18_25, 25_35, 35_plus, skip")
    feedback_text: Optional[str] = Field(None, max_length=2000, description="Opsiyonel aciklama")
    dismissed: bool = Field(True, description="True ise bir daha gosterme (default: True)")


class SurveyStatus(BaseModel):
    dismissed: bool
    has_response: bool
    source: Optional[str] = None
    rating: Optional[str] = None
    age_range: Optional[str] = None
    created_at: Optional[str] = None


class SurveyResponse(BaseModel):
    ok: bool
    message: str
    dismissed: bool


# ─── Endpoints ───────────────────────────────────────────

@router.get("/status", response_model=SurveyStatus)
async def get_survey_status(request: Request, user=Depends(get_current_user)):
    """Kullanici daha once anket gormus mu? dismissed mi?"""
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(401, "User ID alinamadi")

    try:
        sb = get_supabase_admin()
        result = (
            sb.table("survey_responses")
            .select("dismissed, source, rating, age_range, created_at")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        if not result.data:
            return SurveyStatus(dismissed=False, has_response=False)
        return SurveyStatus(
            dismissed=result.data.get("dismissed", False),
            has_response=True,
            source=result.data.get("source"),
            rating=result.data.get("rating"),
            age_range=result.data.get("age_range"),
            created_at=result.data.get("created_at"),
        )
    except Exception as e:
        logger.error("survey status error: %s", e)
        raise HTTPException(500, f"Survey status alinamadi: {e}")


@router.post("", response_model=SurveyResponse)
async def submit_survey(payload: SurveySubmit, request: Request, user=Depends(get_current_user)):
    """Anket gonder. UPSERT (kullanici basina tek satir)."""
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(401, "User ID alinamadi")

    # Validation
    if payload.source and payload.source not in VALID_SOURCES:
        raise HTTPException(400, f"Gecersiz source: {payload.source}")
    if payload.rating and payload.rating not in VALID_RATINGS:
        raise HTTPException(400, f"Gecersiz rating: {payload.rating}")
    if payload.age_range and payload.age_range not in VALID_AGE_RANGES:
        raise HTTPException(400, f"Gecersiz age_range: {payload.age_range}")

    try:
        sb = get_supabase_admin()
        # UPSERT — user_id unique, varsa update yoksa insert
        result = (
            sb.table("survey_responses")
            .upsert({
                "user_id": user_id,
                "source": payload.source or "skip",
                "rating": payload.rating or "skip",
                "age_range": payload.age_range or "skip",
                "feedback_text": payload.feedback_text,
                "dismissed": payload.dismissed,
            }, on_conflict="user_id")
            .execute()
        )
        return SurveyResponse(
            ok=True,
            message="Tesekkurler! Gorusun bizim icin degerli." if not payload.dismissed or payload.source else "Anket atlandi.",
            dismissed=payload.dismissed,
        )
    except Exception as e:
        logger.error("survey submit error: %s", e)
        raise HTTPException(500, f"Survey kaydedilemedi: {e}")
