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

    # 📌 Bug fix: created_at'e guvenme (DB default NOW() eski sorular icin yanlis).
    # Bunun yerine question.id kullan: buyuk id = yeni.
    # Yine de DB created_at varsa onu tercih et (gercek tarih).
    max_id = max((q.id for q in ALL_QUESTIONS), default=88)

    def _effective_date(qid: int, db_created: str) -> float:
        """Soru icin etkili tarih: DB tarihi veya id-bazli fallback."""
        if db_created:
            try:
                return datetime.fromisoformat(db_created.replace("Z", "")).timestamp()
            except Exception:
                pass
        # ID bazli: max_id=88 ise 1=eski, 88=yeni
        # 1 gun = 86400 saniye; id 88 = bugun, id 1 = 87 gun once
        return (max_id - qid) * 86400  # kucuk sayi = yeni

    # ─── 1) Öneriler (personalized) ───
    scored = []
    for q in ALL_QUESTIONS:
        qd_db = db_stats.get(q.id) or {}
        qd = {
            "id": q.id,
            "category": q.category,
            "level": q.level,
            "created_at": qd_db.get("created_at", ""),
            "view_count": qd_db.get("view_count", 0) or 0,
            "attempt_count": qd_db.get("attempt_count", 0) or 0,
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
    # Buyuk ID = yeni. DB created_at bos/None ise ID-bazli kullan.
    recent = sorted(
        scored,
        key=lambda x: _effective_date(x["id"], x["created_at"]),
        reverse=True,
    )[:5]
    for r in recent:
        r["section"] = "recent"
        days = _days_since(r["created_at"]) if r["created_at"] else (max_id - r["id"])
        r["reason"] = f"🆕 #{r['id']} — yakın zamanda" if days < 30 else f"🆕 #{r['id']}"

    # ─── 3) En Çok Gösterilenler (popularity) ───
    # view_count + attempt_count 0 ise "popüler" anlamsız, bunun yerine
    # ID-bazli bir "klasikler" sıralaması yap (düşük ID = eski ama popüler temel sorular)
    pop_with_views = [s for s in scored if s["view_count"] + s["attempt_count"] > 0]
    if pop_with_views:
        popularity = sorted(
            pop_with_views,
            key=lambda x: x["view_count"] + x["attempt_count"] * 2,
            reverse=True,
        )[:5]
        for p in popularity:
            p["section"] = "popular"
            v = p["view_count"] + p["attempt_count"]
            p["reason"] = f"🔥 {v} etkileşim"
    else:
        # Henuz view yoksa: klasik temel sorular (ID 1-15, en cok tercih edilenler)
        popularity = [s for s in scored if 1 <= s["id"] <= 15][:5]
        for p in popularity:
            p["section"] = "popular"
            p["reason"] = "🔥 Klasik — mülakatlarda sıkça çıkıyor"

    # ─── 1) Öneriler (personalized) — şu anki seviyende, çözülmemiş benzer ───
    # Sadece henüz çözülmemiş + success_rate uyumlu seviyede
    if user_ctx["success_rate"] >= 0.7:
        current_level = "advanced"
    elif user_ctx["success_rate"] >= 0.3:
        current_level = "intermediate"
    else:
        current_level = "beginner"

    personal = [
        s for s in scored
        if s["id"] not in user_ctx.get("solved_ids", [])
        and s["level"] == current_level
    ]
    personal = sorted(personal, key=lambda x: x["score"], reverse=True)[:5]
    for p in personal:
        p["section"] = "personal"
        # reason zaten var

    # Eğer hiç öneri yoksa (henüz soru çözülmemiş veya level'de yoksa)
    # → ilk 5'i fallback olarak göster
    if not personal:
        personal = sorted(scored, key=lambda x: x["score"], reverse=True)[:5]

    # ─── 4) Tavsiye Edilenler (next-level) — bir üst seviye ───
    level_order = ["beginner", "intermediate", "advanced"]
    current_idx = level_order.index(current_level) if current_level in level_order else 0
    target_idx = min(current_idx + 1, len(level_order) - 1)
    target_level = level_order[target_idx]

    recommended = [
        s for s in scored
        if s["level"] == target_level
        and s["id"] not in user_ctx.get("solved_ids", [])
    ]
    if not recommended:
        # Beginner'daysan henuz intermediate yoksa → mevcut seviyede en iyileri
        recommended = sorted(
            [s for s in scored if s["id"] not in user_ctx.get("solved_ids", [])],
            key=lambda x: x["score"], reverse=True
        )[:5]
        for r in recommended:
            r["reason"] = "🌱 Mevcut seviyende gelişim için"
    else:
        recommended = sorted(recommended, key=lambda x: x["score"], reverse=True)[:5]
        for r in recommended:
            r["reason"] = f"🚀 Sıradaki seviye ({target_level}) — başarı oranın geçiş için yeterli"

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