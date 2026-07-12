"""
routers/analytics.py
Page view tracking ve aggregate istatistikler.

Endpoints (prefix /api/v2/analytics):
  POST /track                    → sayfa ziyareti kaydet (anonim, public)
  GET  /top-pages                → en cok ziyaret edilen sayfalar (admin)
  GET  /recent                   → son ziyaretler (admin)
  GET  /stats                    → aggregate istatistikler (admin)
  GET  /category-breakdown       → kategori bazli (admin)

KVKK:
  - ip: sadece istatistik icin, anonymize (son octet 0)
  - user_id: Supabase auth (login olmus ziyaretci)
  - session_id: client tarafindan uretilen rastgele ID (cookie'siz)
  - raw 30 gun sonra purge edilebilir (ileride)
"""

import os
import re
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel, Field
from supabase_client import get_supabase, get_supabase_admin

log = logging.getLogger("pymulakat.analytics")

router = APIRouter(prefix="/api/v2/analytics", tags=["analytics"])

IP_REGEX = re.compile(r"^(\d+)\.(\d+)\.(\d+)\.(\d+)$")


def anonymize_ip(ip: str) -> str:
    """KVKK: IP son octet'i 0 yap (analytics için yeterli, bireysel takip yok)."""
    if not ip:
        return ""
    m = IP_REGEX.match(ip)
    if not m:
        return ip
    return f"{m.group(1)}.{m.group(2)}.{m.group(3)}.0"


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


def get_user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "")[:500]


def extract_category(path: str) -> Optional[str]:
    """/temelleri/palindrome → 'temelleri' gibi ilk segmenti al."""
    parts = path.strip("/").split("/")
    if not parts or not parts[0]:
        return None
    # /api/, /admin/, /_next/, /_vercel/ → kategori yok
    if parts[0] in ("api", "admin", "_next", "_vercel", "static"):
        return None
    return parts[0]


def hash_session(session_id: str) -> str:
    """Session ID hash'le (KVKK, geri dondurulemez unique)."""
    return hashlib.sha256(session_id.encode()).hexdigest()[:32]


# ═══════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════

class TrackRequest(BaseModel):
    path: str = Field(..., max_length=500)
    referrer: Optional[str] = Field(None, max_length=500)
    session_id: str = Field(..., min_length=8, max_length=64)


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════

@router.post("/track")
def track_page_view(req: TrackRequest, request: Request):
    """Sayfa ziyaretini kaydet (public, auth gerektirmez).
    
    Body: { path, referrer?, session_id }
    
    Akış:
    1. Anonim IP'yi anonymize et
    2. session_id hash'le (KVKK)
    3. page_views tablosuna INSERT
    4. page_views_daily aggregate UPSERT (counter++)
    
    Rate limit: client tarafında throttle (her 5s)
    """
    path = req.path.strip()
    if not path.startswith("/"):
        path = "/" + path
    
    # API/admin/_next → track etme (gereksiz)
    if path.startswith(("/api/", "/admin/", "/_next/", "/_vercel/")):
        return {"ok": True, "skipped": True}
    
    ip = anonymize_ip(get_client_ip(request))
    ua = get_user_agent(request)
    session_hash = hash_session(req.session_id)
    category = extract_category(path)
    today = datetime.now(timezone.utc).date().isoformat()
    
    sb_admin = get_supabase_admin()
    try:
        # 1) Raw insert
        sb_admin.table("page_views").insert({
            "path": path,
            "category": category,
            "ip": ip,
            "user_agent": ua,
            "referrer": (req.referrer or "")[:500],
            "session_id": session_hash,
        }).execute()
        
        # 2) Daily aggregate (UPSERT — counter++)
        # Supabase'te ON CONFLICT için RPC veya upsert kullan
        sb_admin.rpc("increment_page_view_daily", {
            "p_path": path,
            "p_category": category,
            "p_date": today,
        }).execute()
        
        return {"ok": True}
    except Exception as e:
        # Increment RPC yoksa fallback: doğrudan SELECT + UPDATE
        try:
            existing = sb_admin.table("page_views_daily").select("*").eq("path", path).eq("view_date", today).maybe_single().execute()
            if existing.data:
                new_count = existing.data["view_count"] + 1
                sb_admin.table("page_views_daily").update({"view_count": new_count}).eq("path", path).eq("view_date", today).execute()
            else:
                sb_admin.table("page_views_daily").insert({
                    "path": path,
                    "category": category,
                    "view_date": today,
                    "view_count": 1,
                    "unique_sessions": 0,
                }).execute()
            return {"ok": True}
        except Exception as e2:
            log.error(f"[analytics] track failed: {e2}")
            # Sessizce return (analytics kullanicinin deneyimini bozmamali)
            return {"ok": False}


@router.get("/top-pages")
def top_pages(limit: int = 50, days: int = 30):
    """En cok ziyaret edilen sayfalar (admin only)."""
    sb_admin = get_supabase_admin()
    try:
        # Son N gun
        since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
        result = sb_admin.table("page_views_daily").select("path, category, view_count, view_date").gte("view_date", since).order("view_count", desc=True).limit(limit * 5).execute()
        
        # Path bazli grupla + topla
        path_totals: dict = {}
        for r in (result.data or []):
            p = r["path"]
            if p not in path_totals:
                path_totals[p] = {"path": p, "category": r.get("category"), "total_views": 0, "days": 0}
            path_totals[p]["total_views"] += r.get("view_count", 0)
            path_totals[p]["days"] += 1
        
        sorted_pages = sorted(path_totals.values(), key=lambda x: x["total_views"], reverse=True)[:limit]
        return {"pages": sorted_pages, "total": len(sorted_pages), "days": days}
    except Exception as e:
        log.error(f"[analytics] top_pages failed: {e}")
        raise HTTPException(500, f"Failed: {e}")


@router.get("/recent")
def recent_views(limit: int = 50):
    """Son ziyaretler (admin only)."""
    sb_admin = get_supabase_admin()
    try:
        result = sb_admin.table("page_views").select("path, category, ip, created_at").order("created_at", desc=True).limit(min(limit, 200)).execute()
        return {"views": result.data or [], "total": len(result.data or [])}
    except Exception as e:
        log.error(f"[analytics] recent failed: {e}")
        raise HTTPException(500, f"Failed: {e}")


@router.get("/stats")
def stats(days: int = 30):
    """Aggregate istatistikler (admin only)."""
    sb_admin = get_supabase_admin()
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
        result = sb_admin.table("page_views_daily").select("*").gte("view_date", since).execute()
        rows = result.data or []
        total_views = sum(r.get("view_count", 0) for r in rows)
        unique_paths = len({r["path"] for r in rows})
        unique_categories = len({r["category"] for r in rows if r.get("category")})
        return {
            "total_views": total_views,
            "unique_paths": unique_paths,
            "unique_categories": unique_categories,
            "days": days,
            "daily_rows": len(rows),
        }
    except Exception as e:
        log.error(f"[analytics] stats failed: {e}")
        raise HTTPException(500, f"Failed: {e}")


@router.get("/category-breakdown")
def category_breakdown(days: int = 30):
    """Kategori bazlı ziyaret istatistikleri (admin only)."""
    sb_admin = get_supabase_admin()
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
        result = sb_admin.table("page_views_daily").select("category, view_count").gte("view_date", since).execute()
        rows = result.data or []
        cat_totals: dict = {}
        for r in rows:
            cat = r.get("category") or "(other)"
            cat_totals[cat] = cat_totals.get(cat, 0) + r.get("view_count", 0)
        sorted_cats = [{"category": k, "views": v} for k, v in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)]
        return {"categories": sorted_cats, "days": days}
    except Exception as e:
        log.error(f"[analytics] category_breakdown failed: {e}")
        raise HTTPException(500, f"Failed: {e}")
