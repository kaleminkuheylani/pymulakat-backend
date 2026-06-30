# backend/routers/categories.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

try:
    from question_loader import get_categories
except ImportError:
    def get_categories():
        return []

router = APIRouter(prefix="/api/v2/categories", tags=["categories-v2"])


class CategoryOut(BaseModel):
    slug: str
    label: str
    description: Optional[str] = None
    icon: Optional[str] = None
    question_count: int = 0


class CategoriesResponse(BaseModel):
    data: list[CategoryOut]


@router.get("", response_model=CategoriesResponse)
def list_categories():
    cats = get_categories()
    return CategoriesResponse(data=[CategoryOut(**c) for c in cats])


@router.get("/{category_slug}", response_model=CategoryOut)
def get_category(category_slug: str):
    cats = get_categories()
    cat = next((c for c in cats if c["slug"] == category_slug), None)
    if not cat:
        raise HTTPException(404, f"Kategori bulunamadı")
    return CategoryOut(**cat)