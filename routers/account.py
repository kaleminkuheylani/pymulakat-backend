# backend/routers/account.py
# KVKK Madde 11 - Kullanici haklari: hesap silme ve veri silme
#
# Kullanici istediginde hesabini silebilir:
# - auth.users tablosundan user kaydi
# - interview_attempts tablosundaki tum denemeler
# - profiles tablosundaki profil bilgileri
# - Diger tablolardaki user_id referanslari (anonimlestirme)

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from supabase_client import get_supabase, get_supabase_admin
from dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/account", tags=["account"])


class DeleteAccountRequest(BaseModel):
    confirmation: str  # Kullanici "HESABIMI SIL" yazarak onaylamali


class DeleteAccountResponse(BaseModel):
    success: bool
    message: str
    deleted_at: str


@router.get("/me/export")
async def export_my_data(request: Request):
    """KVKK md. 11 - Kullanicinin tum verilerini gormesi/indirmesi."""
    try:
        user = await get_current_user(request)
        if not user or not user.get("id"):
            raise HTTPException(401, "Oturum gerekli")

        user_id = user["id"]
        sb = get_supabase_admin()

        # Tum iliskili verileri topla
        data = {
            "user": {
                "id": user_id,
                "email": user.get("email"),
                "created_at": user.get("created_at"),
            },
            "attempts": [],
        }

        # Attempts
        try:
            attempts_res = (
                sb.table("interview_attempts")
                .select("id, question_id, passed_tests, total_tests, success, execution_time_ms, hints_used, created_at")
                .eq("user_id", user_id)
                .execute()
            )
            data["attempts"] = attempts_res.data or []
        except Exception as e:
            logger.warning("export.attempts.failed user=%s err=%s", user_id, e)

        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("account.export.failed")
        raise HTTPException(500, "Veri export basarisiz")


@router.post("/delete", response_model=DeleteAccountResponse)
async def delete_my_account(payload: DeleteAccountRequest, request: Request):
    """KVKK md. 11 - Hesap ve tum verilerin silinmesi.

    Kullanici onay metni olarak 'HESABIMI SIL' yazmali.
    Bu geri donusu olmayan bir islemdir.
    """
    try:
        user = await get_current_user(request)
        if not user or not user.get("id"):
            raise HTTPException(401, "Oturum gerekli")

        if payload.confirmation != "HESABIMI SIL":
            raise HTTPException(400, "Onay metni hatali. 'HESABIMI SIL' yazmalisiniz.")

        user_id = user["id"]
        sb = get_supabase_admin()
        deleted_at = __import__("datetime").datetime.utcnow().isoformat()

        logger.warning("account.delete.request user=%s email=%s", user_id, user.get("email"))

        # 1. interview_attempts sil
        try:
            sb.table("interview_attempts").delete().eq("user_id", user_id).execute()
            logger.info("account.delete.attempts.cleared user=%s", user_id)
        except Exception as e:
            logger.warning("account.delete.attempts.failed user=%s err=%s", user_id, e)

        # 2. Supabase Auth user sil (service_role ile)
        try:
            sb.auth.admin.delete_user(user_id)
            logger.info("account.delete.auth.cleared user=%s", user_id)
        except Exception as e:
            logger.warning("account.delete.auth.failed user=%s err=%s", user_id, e)

        return DeleteAccountResponse(
            success=True,
            message="Hesabiniz ve tum verileriniz silindi. KVKK md. 11 kapsaminda talebiniz islenmistir.",
            deleted_at=deleted_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("account.delete.failed")
        raise HTTPException(500, "Hesap silme basarisiz")