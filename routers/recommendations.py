# backend/routers/recommendations.py
# Deterministic, content-based recommendation engine.
#
# Akış sayfası 4 bölüm sunar:
#   1) Öneriler (personalized)   → user_ctx + kategori eşleşmesi
#   2) Son Eklenenler (recent)  → created_at DESC, max 5
#   3) En Çok Gösterilenler (popular) → view_count + attempt_count
#   4) Tavsiye Edilenler (next_level) → success_rate'e göre zorluk atlama
#   + Topluluk tab'ı (forms) → ayrı döner
#
# ML yok, saf fonksiyonlar.

from fastapi import APIRouter, Request, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
from dependencies import get_current_user, get_supabase_admin

router = APIRouter(prefix="/api/v2/recommendations", tags=["recommendations"])


# ─── Scoring Weights ───────────────────────────────
W_CATEGORY_MATCH = 30
W_DIFFICULTY_MATCH = 20
W_FRESHNESS = 15
W_TUTORIAL_BRIDGE = 15
W_POPULARITY = 12
W_RECENCY_POPULARITY = 8


# ─── Helpers ──────────────────────────────────────
def _days_since(iso_str: str) -> float:
    if not iso_str:
        return 9999
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", ""))
        return (datetime.utcnow() - dt).total_seconds() / 86400
    except Exception:
        return 9999


async def _build_user_context(user_id: str) -> Dict:
    """Kullanıcı denemelerinden bağlam çıkar."""
    sb = get_supabase_admin()
    ctx: Dict[str, Any] = {
        "user_id": user_id,
        "top_categories": [],
        "weak_categories": [],
        "success_rate": 0,
        "solved_ids": [],
        "total_attempts": 0,
    }
    try:
        attempts_res = (
            sb.table("interview_attempts")
            .select("question_id, passed, category, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        attempts = attempts_res.data or []
        if not attempts:
            return ctx

        ctx["solved_ids"] = [a["question_id"] for a in attempts if a.get("passed")]
        ctx["total_attempts"] = len(attempts)

        cat_stats: Dict[str, Dict[str, int]] = {}
        for a in attempts:
            cat = a.get("category") or "unknown"
            cat_stats.setdefault(cat, {"passed": 0, "total": 0})
            cat_stats[cat]["total"] += 1
            if a.get("passed"):
                cat_stats[cat]["passed"] += 1

        cat_success_rate = {
            cat: stats["passed"] / stats["total"]
            for cat, stats in cat_stats.items()
            if stats["total"] >= 2
        }
        sorted_cats = sorted(cat_success_rate.items(), key=lambda x: -x[1])
        ctx["top_categories"] = [c for c, _ in sorted_cats[:3]]
        ctx["weak_categories"] = [c for c, r in cat_success_rate.items() if r < 0.5]
        ctx["success_rate"] = sum(s["passed"] for s in cat_stats.values()) / len(attempts)
    except Exception:
        pass
    return ctx


# ─── Personal Score ───────────────────────────────
def _personal_score(q: Dict, ctx: Dict) -> float:
    s = 0.0
    if q["category"] in ctx.get("top_categories", []):
        idx = ctx["top_categories"].index(q["category"])
        s += W_CATEGORY_MATCH * (1 - idx * 0.2)
    if ctx["success_rate"] < 0.3 and q["level"] == "beginner":
        s += W_DIFFICULTY_MATCH
    elif 0.3 <= ctx["success_rate"] < 0.7 and q["level"] == "intermediate":
        s += W_DIFFICULTY_MATCH
    elif ctx["success_rate"] >= 0.7 and q["level"] == "advanced":
        s += W_DIFFICULTY_MATCH
    if q["id"] not in ctx.get("solved_ids", []):
        s += 5
    return s


# ─── Endpoint: Akış (4 bölüm) ─────────────────────
@router.get("/flow")
async def get_flow(
    request: Request,
    refresh: bool = Query(False, description="Cache bypass"),
):
    """Kişiselleştirilmiş akış — 4 bölüm, her biri max 5 item."""
    from data.QUESTIONS import QUESTIONS as ALL_QUESTIONS

    user_ctx: Dict[str, Any] = {
        "top_categories": ["python-basics"],
        "weak_categories": [],
        "success_rate": 0,
        "solved_ids": [],
    }
    is_authenticated = False
    try:
        user = await get_current_user(request)
        is_authenticated = True
        user_ctx = await _build_user_context(user["id"])
    except HTTPException:
        pass

    # DB'den view_count + attempt_count çek (popülerlik için)
    db_stats: Dict[int, Dict] = {}
    try:
        sb = get_supabase_admin()
        rows = sb.table("interwiews").select("id, view_count, attempt_count, created_at").execute()
        db_stats = {r["id"]: r for r in (rows.data or [])}
    except Exception:
        pass

    # ─── 1) Öneriler (personalized) ───
    scored = []
    for q in ALL_QUESTIONS:
        qd = {
            "id": q.id,
            "category": q.category,
            "level": q.level,
            "created_at": (db_stats.get(q.id) or {}).get("created_at", ""),
            "view_count": (db_stats.get(q.id) or {}).get("view_count", 0) or 0,
            "attempt_count": (db_stats.get(q.id) or {}).get("attempt_count", 0) or 0,
        }
        personal = _personal_score(qd, user_ctx)
        # Kategori bonus: zayıf kategoriye daha düşük ağırlık
        if qd["category"] in user_ctx.get("weak_categories", []):
            personal += W_TUTORIAL_BRIDGE
        scored.append({
            "type": "question",
            "id": q.id,
            "title": q.title,
            "category": q.category,
            "level": q.level,
            "slug": getattr(q, "slug", None),
            "score": personal,
            "reason": _explain_personal(q.category, q.level, user_ctx),
            "created_at": qd["created_at"],
            "view_count": qd["view_count"],
            "attempt_count": qd["attempt_count"],
        })

    # ─── 2) Son Eklenenler (freshness) ───
    recent = sorted(scored, key=lambda x: x["created_at"], reverse=True)[:5]
    for r in recent:
        r["section"] = "recent"
        r["reason"] = f"🆕 {_days_since(r['created_at']):.0f} gün önce eklendi" if r["created_at"] else "🆕 Yeni"

    # ─── 3) En Çok Gösterilenler (popularity) ───
    popularity = sorted(scored, key=lambda x: x["view_count"] + x["attempt_count"] * 2, reverse=True)[:5]
    for p in popularity:
        p["section"] = "popular"
        views = p["view_count"] + p["attempt_count"]
        p["reason"] = f"🔥 {views} etkileşim" if views > 0 else "🔥 Popüler"

    # ─── 4) Tavsiye Edilenler (next-level) ───
    # Kullanıcının success_rate'ine göre bir üst seviyeden öner
    if user_ctx["success_rate"] >= 0.7:
        target_level = "advanced"
    elif user_ctx["success_rate"] >= 0.3:
        target_level = "intermediate"
    else:
        target_level = "beginner"

    recommended = [
        s for s in scored
        if s["level"] == target_level and s["id"] not in user_ctx.get("solved_ids", [])
    ]
    recommended = sorted(recommended, key=lambda x: x["score"], reverse=True)[:5]
    for r in recommended:
        r["section"] = "recommended"
        r["reason"] = f"🎯 {target_level.capitalize()} seviye — başarı oranına göre sıradaki"

    # ─── Öneriler (personalized, ayrı liste) ───
    personal = sorted(scored, key=lambda x: x["score"], reverse=True)[:5]
    for p in personal:
        p["section"] = "personal"
        # reason zaten var

    return {
        "sections": {
            "personal": personal,
            "recent": recent,
            "popular": popularity,
            "recommended": recommended,
        },
        "context": {
            "is_authenticated": is_authenticated,
            "top_categories": user_ctx.get("top_categories", []),
            "success_rate": round(user_ctx.get("success_rate", 0), 2),
            "target_level": target_level,
        },
    }


# ─── Endpoint: Topluluk (formlar) ──────────────────
@router.get("/community")
async def get_community(
    limit: int = Query(15, le=50),
):
    """Topluluk tab'ı — form paylaşımları, tartışmalar."""
    try:
        sb = get_supabase_admin()
        forms_res = (
            sb.table("forms")
            .select("*, replies:form_replies(count)")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        items = []
        for f in (forms_res.data or []):
            reply_count = 0
            if f.get("replies") and isinstance(f["replies"], list) and f["replies"]:
                reply_count = f["replies"][0].get("count", 0)
            items.append({
                "type": "form",
                "id": f["id"],
                "title": f["title"],
                "body": f["body"],
                "category": f["category"],
                "tags": f.get("tags") or [],
                "reply_count": reply_count,
                "created_at": f["created_at"],
                "reason": _explain_form(reply_count, f["created_at"]),
            })
        return {"data": items}
    except Exception:
        return {"data": []}


# ─── Reason Helpers ───────────────────────────────
def _explain_personal(category: str, level: str, ctx: Dict) -> str:
    if category in ctx.get("top_categories", []):
        return f"🔁 {category} kategorisinde başarılısın"
    if category in ctx.get("weak_categories", []):
        return "💪 Zorlandığın kategoride gelişim için"
    if ctx.get("success_rate", 0) < 0.3 and level == "beginner":
        return "🌱 Başlangıç seviyesi, seni güçlendirir"
    return "✨ Sana özel"


def _explain_form(reply_count: int, created_at: str) -> str:
    days = _days_since(created_at)
    if reply_count > 5:
        return f"🔥 Aktif tartışma ({reply_count} yanıt)"
    if days <= 3:
        return "🆕 Yeni paylaşım"
    return "💬 Topluluk"


# ─── Eski endpoint (geriye uyumlu) ─────────────────
@router.get("")
async def get_recommendations_compat(
    request: Request,
    limit: int = 10,
):
    """Geriye uyumluluk — eski client'lar için düz liste."""
    flow = await get_flow(request=request, refresh=False)
    all_items = []
    for section in flow["sections"].values():
        all_items.extend(section)
    all_items.sort(key=lambda x: x.get("score", 0), reverse=True)
    return {
        "data": all_items[:limit],
        "context": flow["context"],
    }