# backend/routers/recommendations.py
# Deterministic, content-based recommendation engine.
# Giriş: user'in profil verileri (success/fail, son çözdüğü sorular, seviye)
# Çıkış: karışık liste — yeni sorular + yeni rehberler + form paylaşımları
# Makine öğrenmesi YOK — saf scoring fonksiyonları.

from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime
from dependencies import get_current_user, get_supabase_admin

router = APIRouter(prefix="/api/v2/recommendations", tags=["recommendations"])


# ─── Scoring Weights (sabit, kolay tuning) ────────────
W_CATEGORY_MATCH = 30      # Kullanıcının başarılı olduğu kategori
W_DIFFICULTY_MATCH = 20    # Kullanıcının seviyesiyle uyum
W_FRESHNESS = 15           # Yeni içerik bonusu (son 14 gün)
W_TUTORIAL_BRIDGE = 15     # Henüz çözülmemiş rehberler
W_RELATED_DIVERSITY = 10   # Çok bağlantılı ama az çözülmüş
W_FORM_ENGAGEMENT = 10     # Aktif formlar (yanıt almış)


def _score_question(q: Dict, user_ctx: Dict) -> float:
    """Bir soru için kişiselleştirilmiş skor."""
    score = 0.0

    # 1) Kategori eşleşmesi
    user_top_cats = user_ctx.get("top_categories", [])
    if q["category"] in user_top_cats:
        idx = user_top_cats.index(q["category"])
        # İlk kategoriye max, sonrakine azalan
        score += W_CATEGORY_MATCH * (1 - idx * 0.2)

    # 2) Zorluk eşleşmesi (kullanıcının success_rate'ine göre)
    success_rate = user_ctx.get("success_rate", 0)
    q_level = q.get("level", "beginner")
    if success_rate < 0.3 and q_level == "beginner":
        score += W_DIFFICULTY_MATCH
    elif 0.3 <= success_rate < 0.7 and q_level == "intermediate":
        score += W_DIFFICULTY_MATCH
    elif success_rate >= 0.7 and q_level == "advanced":
        score += W_DIFFICULTY_MATCH

    # 3) Freshness — yeni sorular (84-88 gibi son 14 gün)
    created = q.get("created_at", "")
    if created:
        try:
            days = (datetime.utcnow() - datetime.fromisoformat(created.replace("Z", ""))).days
            if days <= 14:
                score += W_FRESHNESS * (1 - days / 14)
        except Exception:
            pass

    # 4) Henüz çözülmemiş mi?
    solved = user_ctx.get("solved_ids", [])
    if q["id"] not in solved:
        score += 5  # küçük bonus

    return score


def _score_tutorial(t: Dict, user_ctx: Dict) -> float:
    """Bir rehber için kişiselleştirilmiş skor."""
    score = 0.0

    # Kullanıcının başarısız olduğu kategorilerde rehber daha değerli
    weak_cats = user_ctx.get("weak_categories", [])
    if t.get("category") in weak_cats:
        score += W_TUTORIAL_BRIDGE * 1.2

    # Kategori eşleşmesi
    user_top_cats = user_ctx.get("top_categories", [])
    if t.get("category") in user_top_cats:
        score += W_CATEGORY_MATCH * 0.5

    # Freshness
    created = t.get("created_at") or t.get("published_at", "")
    if created:
        try:
            days = (datetime.utcnow() - datetime.fromisoformat(created.replace("Z", ""))).days
            if days <= 14:
                score += W_FRESHNESS
        except Exception:
            pass

    return score


def _score_form(f: Dict) -> float:
    """Form için skor — yeni + yanıt almış + çok etkileşim."""
    score = W_FORM_ENGAGEMENT  # base

    # Yanıt sayısı
    reply_count = f.get("replies_count", 0) or 0
    score += min(reply_count * 2, 20)

    # Freshness
    created = f.get("created_at", "")
    if created:
        try:
            days = (datetime.utcnow() - datetime.fromisoformat(created.replace("Z", ""))).days
            if days <= 7:
                score += W_FRESHNESS
        except Exception:
            pass

    return score


@router.get("")
async def get_recommendations(
    request: Request,
    limit: int = 10,
):
    """
    Kullanıcıya özel öneriler.
    Login olmadan: genel popüler içerikler (yeni + çok çözülen).
    Login olunca: kişiselleştirilmiş.
    """
    from data.QUESTIONS import QUESTIONS as ALL_QUESTIONS
    from routers.tutorials import FALLBACK_TUTORIALS

    user_ctx: Dict[str, Any] = {
        "top_categories": [],
        "weak_categories": [],
        "success_rate": 0,
        "solved_ids": [],
    }

    # Kullanıcı giriş yapmışsa kişiselleştir
    try:
        user = await get_current_user(request)
        user_ctx = await _build_user_context(user["id"])
    except HTTPException:
        # Login değil — anonim context, sadece yenilik kriteri
        pass

    # ─── 1) Soruları puanla ───
    q_scores = []
    for q in ALL_QUESTIONS:
        score = _score_question(
            {
                "id": q.id,
                "category": q.category,
                "level": q.level,
                "created_at": getattr(q, "created_at", ""),
            },
            user_ctx,
        )
        q_scores.append({
            "type": "question",
            "id": q.id,
            "title": q.title,
            "category": q.category,
            "level": q.level,
            "slug": getattr(q, "slug", None),
            "score": score,
            "reason": _explain_question_reason(q, user_ctx),
        })

    # ─── 2) Rehberleri puanla ───
    t_scores = []
    for slug, t in FALLBACK_TUTORIALS.items():
        score = _score_tutorial(
            {
                "category": t.get("category"),
                "created_at": "",  # FALLBACK'lerde yok
            },
            user_ctx,
        )
        t_scores.append({
            "type": "tutorial",
            "id": t.get("id"),
            "slug": slug,
            "title": t.get("title"),
            "category": t.get("category"),
            "score": score,
            "reason": _explain_tutorial_reason(t, user_ctx),
        })

    # ─── 3) Form'ları puanla (varsa) ───
    f_scores: List[Dict] = []
    try:
        sb = get_supabase_admin()
        forms_res = (
            sb.table("forms")
            .select("*, replies:form_replies(count)")
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        for f in (forms_res.data or []):
            f["replies_count"] = f.get("replies", [{}])[0].get("count", 0) if f.get("replies") else 0
            score = _score_form(f)
            f_scores.append({
                "type": "form",
                "id": f["id"],
                "title": f["title"],
                "category": f["category"],
                "score": score,
                "reason": _explain_form_reason(f),
            })
    except Exception:
        # Tablo henüz yoksa boş geç
        pass

    # ─── Birleştir + sırala ───
    all_items = q_scores + t_scores + f_scores
    all_items.sort(key=lambda x: x["score"], reverse=True)

    return {
        "data": all_items[:limit],
        "context": {
            "is_authenticated": bool(user_ctx.get("user_id")),
            "top_categories": user_ctx.get("top_categories", []),
        },
    }


async def _build_user_context(user_id: str) -> Dict:
    """Kullanıcı denemelerinden bağlam oluştur."""
    sb = get_supabase_admin()
    ctx: Dict[str, Any] = {
        "user_id": user_id,
        "top_categories": [],
        "weak_categories": [],
        "success_rate": 0,
        "solved_ids": [],
    }

    try:
        # Son 50 denemeyi çek
        attempts_res = (
            sb.table("attempts")
            .select("question_id, passed, category")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        attempts = attempts_res.data or []
        if not attempts:
            return ctx

        # Çözülenler
        ctx["solved_ids"] = [a["question_id"] for a in attempts if a.get("passed")]

        # Kategori başarı oranı
        cat_stats: Dict[str, Dict[str, int]] = {}
        for a in attempts:
            cat = a.get("category") or "unknown"
            if cat not in cat_stats:
                cat_stats[cat] = {"passed": 0, "total": 0}
            cat_stats[cat]["total"] += 1
            if a.get("passed"):
                cat_stats[cat]["passed"] += 1

        # Skorla: yüksek success_rate → top_categories
        cat_success_rate = {
            cat: stats["passed"] / stats["total"]
            for cat, stats in cat_stats.items()
            if stats["total"] >= 2
        }
        sorted_cats = sorted(cat_success_rate.items(), key=lambda x: -x[1])
        ctx["top_categories"] = [c for c, _ in sorted_cats[:3]]

        # Zayıf kategoriler (success_rate < 0.5 ve en az 2 deneme)
        ctx["weak_categories"] = [
            cat for cat, rate in cat_success_rate.items() if rate < 0.5
        ]

        # Genel başarı oranı
        total_passed = sum(s["passed"] for s in cat_stats.values())
        ctx["success_rate"] = total_passed / len(attempts) if attempts else 0

    except Exception:
        pass

    return ctx


def _explain_question_reason(q, ctx) -> str:
    """Kullanıcıya gösterilecek kısa açıklama."""
    if q.category in ctx.get("top_categories", []):
        return f"🔁 {q.category} kategorisinde başarılısın, benzer tarz"
    if ctx.get("success_rate", 0) < 0.3 and q.level == "beginner":
        return "🌱 Başlangıç seviyesi, seni güçlendirir"
    return "📌 Yeni içerik"


def _explain_tutorial_reason(t, ctx) -> str:
    if t.get("category") in ctx.get("weak_categories", []):
        return "💪 Zorlandığın kategoride rehber"
    return "📖 Konuyu pekiştirir"


def _explain_form_reason(f) -> str:
    replies = f.get("replies_count", 0) or 0
    if replies > 0:
        return f"💬 Aktif tartışma ({replies} yanıt)"
    return "🆕 Yeni paylaşım"