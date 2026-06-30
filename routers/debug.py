"""Debug endpoint — Supabase tablo/kolon yapısını gör"""
from fastapi import APIRouter, HTTPException
from supabase_client import get_supabase_admin

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/profiles-schema")
def profiles_schema(email: str = None):
    """profiles tablosunun kolonlarını listele. ?email=... ile belirli kullanıcıyı getir."""
    try:
        sb = get_supabase_admin()
        query = sb.table("profiles").select("*")
        if email:
            query = query.eq("email", email)
        result = query.limit(1).execute()
        return {
            "ok": True,
            "data": result.data,
            "error": str(result) if hasattr(result, "error") else None,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "hint": "profiles tablosu yok. Supabase SQL Editor'da CREATE TABLE çalıştır.",
        }


@router.get("/tables")
def list_tables():
    """Supabase'deki public tabloları listele."""
    try:
        sb = get_supabase_admin()
        # RPC ile information_schema'dan çek
        result = sb.rpc("exec_sql", {
            "query": "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
        }).execute()
        return {
            "ok": True,
            "tables": result.data,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "hint": "RPC çalışmadı. Direkt SQL Editor'dan kontrol et.",
        }