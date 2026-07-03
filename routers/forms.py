# backend/routers/forms.py
# Kullanıcı form'ları: feedback, soru yardımı, kod yardımı, yazılım paylaşımı
# Public listeleme (login olmadan), post etme (login gerekli), yanıtlama (login gerekli)

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from dependencies import get_current_user

router = APIRouter(prefix="/api/v2/forms", tags=["forms"])

# ─── Form Kategorileri ────────────────────────────────
CATEGORIES = {
    "feedback": {
        "slug": "feedback",
        "label": "Geri Bildirim",
        "description": "Platform hakkında öneri, şikayet veya beğeni",
        "icon": "💬",
        "color": "amber",
    },
    "question_help": {
        "slug": "question_help",
        "label": "Soru Yardımı",
        "description": "Soruda takıldığın yer, ipucu beklentisi, çözüm tartışması",
        "icon": "❓",
        "color": "indigo",
    },
    "code_help": {
        "slug": "code_help",
        "label": "Kod Yardımı",
        "description": "Kodunun hata ayıklaması, refactoring önerileri, best practice",
        "icon": "🐛",
        "color": "rose",
    },
    "share": {
        "slug": "share",
        "label": "Yazılım Paylaşımı",
        "description": "Proje, kütüphane, kaynak veya deneyim paylaşımı",
        "icon": "🚀",
        "color": "emerald",
    },
}


# ─── Pydantic Models ─────────────────────────────────
class FormCreate(BaseModel):
    category: str = Field(..., description="feedback | question_help | code_help | share")
    title: str = Field(..., min_length=3, max_length=120)
    body: str = Field(..., min_length=10, max_length=5000)
    tags: Optional[List[str]] = []
    related_question_id: Optional[int] = None  # question_help için


class FormReplyCreate(BaseModel):
    body: str = Field(..., min_length=2, max_length=2000)


# ─── Endpoints ───────────────────────────────────────
@router.get("/categories")
async def list_categories():
    """Tüm form kategorileri. Public."""
    return {"data": list(CATEGORIES.values())}


@router.get("")
async def list_forms(
    request: Request,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    """Form listesi. Public — login olmadan da görünür."""
    from dependencies import get_supabase_admin

    try:
        sb = get_supabase_admin()
        query = sb.table("forms").select("*, replies:form_replies(count)").order("created_at", desc=True)

        if category:
            if category not in CATEGORIES:
                raise HTTPException(400, f"Geçersiz kategori: {category}")
            query = query.eq("category", category)

        query = query.range(offset, offset + limit - 1)
        res = query.execute()

        return {"data": res.data or [], "total": len(res.data or [])}
    except HTTPException:
        raise
    except Exception as e:
        # Tablo yoksa boş liste döndür (henüz migrate olmamış olabilir)
        return {"data": [], "total": 0, "warning": str(e)}


@router.get("/{form_id}")
async def get_form(form_id: int):
    """Tek form detayı + tüm yanıtlar. Public."""
    from dependencies import get_supabase_admin

    try:
        sb = get_supabase_admin()
        form_res = (
            sb.table("forms")
            .select("*, replies:form_replies(*)")
            .eq("id", form_id)
            .single()
            .execute()
        )

        if not form_res.data:
            raise HTTPException(404, "Form bulunamadı")

        return {"data": form_res.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Form yüklenemedi: {str(e)}")


@router.post("")
async def create_form(payload: FormCreate, request: Request):
    """Yeni form oluştur. Login gerekli."""
    user = await get_current_user(request)

    if payload.category not in CATEGORIES:
        raise HTTPException(400, f"Geçersiz kategori: {payload.category}")

    from dependencies import get_supabase_admin

    try:
        sb = get_supabase_admin()
        row = {
            "user_id": user["id"],
            "category": payload.category,
            "title": payload.title,
            "body": payload.body,
            "tags": payload.tags or [],
            "related_question_id": payload.related_question_id,
            "created_at": datetime.utcnow().isoformat(),
        }
        res = sb.table("forms").insert(row).execute()

        if not res.data:
            raise HTTPException(500, "Form oluşturulamadı")

        return {"data": res.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Form oluşturulamadı: {str(e)}")


@router.post("/{form_id}/reply")
async def reply_form(form_id: int, payload: FormReplyCreate, request: Request):
    """Forma yanıt ver. Login gerekli."""
    user = await get_current_user(request)

    from dependencies import get_supabase_admin

    try:
        sb = get_supabase_admin()
        row = {
            "form_id": form_id,
            "user_id": user["id"],
            "body": payload.body,
            "created_at": datetime.utcnow().isoformat(),
        }
        res = sb.table("form_replies").insert(row).execute()

        if not res.data:
            raise HTTPException(500, "Yanıt oluşturulamadı")

        return {"data": res.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Yanıt oluşturulamadı: {str(e)}")