"""
Question Reports — Kullanici "Soru hataliysa bildir" butonu.

2026-07-17: Yeni endpoint. Authenticated user screenshot + aciklama ile
soru hatasini bildirebilir. Anonim user (misafir) 401 alir.

Akis:
  1. Frontend "Soru Hataliysa Bildir" butonuna basar
  2. Modal acilir: screenshot (paste/drag) + description textarea
  3. POST /api/v2/question-reports
  4. Backend auth check (Supabase JWT cookie veya Authorization header)
  5. INSERT to question_reports tablosu
  6. 201 Created response
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/question-reports", tags=["question-reports"])


# ─── Pydantic Models ─────────────────────────────────────

class QuestionReportCreate(BaseModel):
    question_id: int = Field(..., gt=0, description="Hatali oldugu dusunulen soru ID")
    question_slug: Optional[str] = Field(None, max_length=200, description="Soru slug (canonical URL icin)")
    category: Optional[str] = Field(None, max_length=50, description="Kategori (algorithms, data-structures, ...)")
    description: str = Field(..., min_length=10, max_length=2000, description="Kullanici aciklamasi (en az 10 karakter)")
    screenshot_base64: Optional[str] = Field(None, description="Base64 inline screenshot (data:image/png;base64,...) veya sadece base64 string")


class QuestionReportResponse(BaseModel):
    id: int
    question_id: int
    status: str
    created_at: str
    message: str = "Raporunuz alindi. Tesekkurler!"


# ─── Auth Dependency ─────────────────────────────────────

async def get_current_user_id(request: Request) -> str:
    """
    Auth check: Supabase JWT (cookie veya Authorization header).
    Returns user_id (UUID). Raises 401 if not authenticated.
    """
    from supabase_client import get_supabase_admin
    
    # 1. Authorization header (Bearer)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            sb = get_supabase_admin()
            # Supabase auth.get_user(token) — JWT verify
            user_response = sb.auth.get_user(token)
            if user_response and user_response.user:
                return user_response.user.id
        except Exception as e:
            logger.warning(f"Bearer auth failed: {e}")

    # 2. Supabase cookie (sb-pymulakat-auth-token, sb-*-auth-token, vs.)
    cookies = request.cookies
    for name, value in cookies.items():
        if "auth-token" in name or "access-token" in name:
            # JWT cookie — Supabase session JSON {"access_token": "...", ...}
            # Veya direkt JWT string
            try:
                sb = get_supabase_admin()
                # JSON parse dene
                import json
                if value.startswith("{"):
                    session = json.loads(value)
                    token = session.get("access_token")
                else:
                    token = value
                if token:
                    user_response = sb.auth.get_user(token)
                    if user_response and user_response.user:
                        return user_response.user.id
            except Exception as e:
                logger.debug(f"Cookie {name} auth parse failed: {e}")
                continue

    raise HTTPException(status_code=401, detail="auth_required")


# ─── Rate Limit (basit, in-memory) ───────────────────────

# TODO: Production icin Redis/Memcached kullan. Simdilik in-memory basit koruma.
_report_count: dict[str, list] = {}

async def check_rate_limit(user_id: str, max_per_hour: int = 5):
    """
    Bir kullanici saatte max 5 rapor gonderebilir.
    Spam korumasi.
    """
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - 3600  # 1 saat once

    user_reports = _report_count.get(user_id, [])
    # Eski kayitlari temizle
    user_reports = [t for t in user_reports if t > cutoff]

    if len(user_reports) >= max_per_hour:
        raise HTTPException(
            status_code=429,
            detail=f"rate_limit: Saatte max {max_per_hour} rapor gonderebilirsiniz. Lutfen bekleyin.",
        )

    user_reports.append(now.timestamp())
    _report_count[user_id] = user_reports


# ─── Routes ──────────────────────────────────────────────

@router.post("", response_model=QuestionReportResponse, status_code=201)
async def create_question_report(
    payload: QuestionReportCreate,
    user_id: str = Depends(get_current_user_id),
):
    """
    Yeni soru raporu olustur (authenticated user).

    Body:
      - question_id (int): Soru ID
      - question_slug (str, optional): Slug
      - category (str, optional): Kategori slug
      - description (str, 10-2000 char): Aciklama
      - screenshot_base64 (str, optional): Base64 inline screenshot

    Returns:
      201: { id, question_id, status, created_at, message }
      401: auth_required
      429: rate_limit
      400: validation error
      500: server error
    """
    try:
        # Rate limit
        await check_rate_limit(user_id)

        from supabase_client import get_supabase_admin
        sb = get_supabase_admin()

        # Screenshot base64 size check (~2MB max, ~2.7MB base64)
        if payload.screenshot_base64:
            size_bytes = len(payload.screenshot_base64) * 3 / 4  # base64 to bytes
            if size_bytes > 2 * 1024 * 1024:  # 2MB
                raise HTTPException(
                    status_code=400,
                    detail="screenshot_too_large: Screenshot 2MB'dan buyuk olamaz.",
                )

        # INSERT
        insert_data = {
            "user_id": user_id,
            "question_id": payload.question_id,
            "question_slug": payload.question_slug,
            "category": payload.category,
            "screenshot_base64": payload.screenshot_base64,
            "description": payload.description,
            "status": "open",
        }
        result = sb.table("question_reports").insert(insert_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="db_insert_failed")

        report = result.data[0]
        logger.info(
            f"Question report created: id={report['id']} user={user_id} "
            f"question_id={payload.question_id} category={payload.category}"
        )

        return QuestionReportResponse(
            id=report["id"],
            question_id=report["question_id"],
            status=report["status"],
            created_at=report["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question report create error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"server_error: {str(e)}")


@router.get("/me")
async def get_my_reports(
    user_id: str = Depends(get_current_user_id),
    limit: int = 20,
):
    """
    Kullanicinin kendi raporlari (dashboard / 'raporlarim' sayfasi icin).
    """
    try:
        from supabase_client import get_supabase_admin
        sb = get_supabase_admin()

        result = (
            sb.table("question_reports")
            .select("id, question_id, question_slug, category, description, status, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return {
            "reports": result.data or [],
            "count": len(result.data or []),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get my reports error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
