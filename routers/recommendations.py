# backend/routers/recommendations.py
# Router → Recommendation Engine köprüsü.
# Asıl iş services/recommendation_engine.py'de (saf, deterministik, test edilebilir).

from fastapi import APIRouter, Request, HTTPException, Query
from dependencies import get_current_user
from supabase_client import get_supabase_admin
from services.recommendation_engine import (
    QuestionLite,
    UserContext,
    build_flow,
    to_api_dict,
    days_since,
)

router = APIRouter(prefix="/api/v2/recommendations", tags=["recommendations"])


# ─── User Context builder (DB'den çek) ──────────────────
async def _build_user_context(user_id: str) -> UserContext:
    """Kullanıcının son 50 attempt'ten bağlam çıkar.

    Spesifik reason üretmek için:
    - solved_ids, attempted_ids
    - top_categories, weak_categories
    - success_rate, total_attempts
    - recent_failed (son başarısız denemeler)
    - no_hint_failed (ipucusuz başarısızlar)
    """
    sb = get_supabase_admin()
    ctx = UserContext(is_authenticated=True, user_id=user_id) if False else UserContext(is_authenticated=True)
    ctx.is_authenticated = True
    try:
        attempts_res = (
            sb.table("interview_attempts")
            .select("question_id, success, hints_used, passed_tests, total_tests, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        attempts = attempts_res.data or []
        if not attempts:
            return ctx

        ctx.solved_ids = list({a["question_id"] for a in attempts if a.get("success")})
        ctx.attempted_ids = list({a["question_id"] for a in attempts})
        ctx.total_attempts = len(attempts)

        # Kategori başarı oranı — question'ları join etmemiz lazım
        # Ancak hızlı yol: attempts'te category yoksa questions tablosundan çek
        q_ids = list({a["question_id"] for a in attempts})
        try:
            q_res = sb.table("interwiews").select("id, category").in_("id", q_ids).execute()
            cat_map = {r["id"]: r.get("category") for r in (q_res.data or [])}
        except Exception:
            cat_map = {}

        cat_stats: dict = {}
        for a in attempts:
            cat = cat_map.get(a["question_id"], "unknown")
            cat_stats.setdefault(cat, {"passed": 0, "total": 0})
            cat_stats[cat]["total"] += 1
            if a.get("success"):
                cat_stats[cat]["passed"] += 1

        cat_success_rate = {
            cat: stats["passed"] / stats["total"]
            for cat, stats in cat_stats.items()
            if stats["total"] >= 2
        }
        sorted_cats = sorted(cat_success_rate.items(), key=lambda x: -x[1])
        ctx.top_categories = [c for c, _ in sorted_cats[:3]]
        ctx.weak_categories = [c for c, r in cat_success_rate.items() if 0 < r < 0.5]
        ctx.success_rate = sum(s["passed"] for s in cat_stats.values()) / max(len(attempts), 1)

        # Son başarısız denemeler (spesifik reason için)
        # Title lazım — join
        try:
            recent_fail_qids = [a["question_id"] for a in attempts[:10] if not a.get("success")][:5]
            if recent_fail_qids:
                rf_res = sb.table("interwiews").select("id, title").in_("id", recent_fail_qids).execute()
                ctx.recent_failed = [(r["id"], r.get("title", "")) for r in (rf_res.data or [])]
                # İpuçusuz başarısızlar
                ctx.no_hint_failed = [
                    a["question_id"] for a in attempts
                    if not a.get("success") and (a.get("hints_used", 0) or 0) == 0
                ][:5]
        except Exception:
            pass

    except Exception:
        pass
    return ctx


# ─── Tüm soruları DB'den çek (QuestionLite listesi) ─────
def _fetch_all_questions() -> list:
    """interwiews tablosundan tüm soruları QuestionLite listesine çevir."""
    sb = get_supabase_admin()
    try:
        rows = sb.table("interwiews").select(
            "id, title, category, level, slug, function_name, view_count, attempt_count, created_at"
        ).execute().data or []
        out = []
        for r in rows:
            out.append(QuestionLite(
                id=int(r.get("id") or 0),
                title=r.get("title") or "",
                category=r.get("category") or "python-basics",
                level=(r.get("level") or "beginner").lower(),
                slug=r.get("slug") or "",
                function_name=r.get("function_name") or "",
                view_count=int(r.get("view_count") or 0),
                attempt_count=int(r.get("attempt_count") or 0),
                created_at=r.get("created_at") or "",
            ))
        return out
    except Exception:
        return []


# ─── Endpoint: Akış ────────────────────────────────────
@router.get("/flow")
async def get_flow(request: Request):
    """Kişiselleştirilmiş akış — 4 section × max 2 item = 6-8 öneri.

    Deterministik: aynı (user, DB state) → aynı sonuç.
    Spesifik reason: kullanıcı attempt'lerine ve istatistiklere dayalı.
    """
    user_ctx = UserContext(is_authenticated=False)
    try:
        user = await get_current_user(request)
        user_ctx = await _build_user_context(user["id"])
    except HTTPException:
        pass  # Misafir akışı — anonim bağlam

    questions = _fetch_all_questions()
    if not questions:
        # DB boşsa fallback hardcoded data'dan çek
        try:
            from data.QUESTIONS import QUESTIONS as ALL_QUESTIONS
            questions = [
                QuestionLite(
                    id=q.id,
                    title=q.title,
                    category=q.category,
                    level=q.level,
                    slug=getattr(q, "slug", "") or "",
                    function_name=getattr(q, "function_name", "") or "",
                    view_count=0,
                    attempt_count=0,
                    created_at="",
                )
                for q in ALL_QUESTIONS
            ]
        except Exception:
            questions = []

    sections, ctx_dict = build_flow(questions, user_ctx)

    return {
        "sections": to_api_dict(sections),
        "context": ctx_dict,
    }


# ─── Endpoint: Topluluk (formlar) ─────────────────────
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
                "reason": _explain_form(reply_count, f.get("created_at", "")),
            })
        return {"data": items}
    except Exception:
        return {"data": []}


def _explain_form(reply_count: int, created_at: str) -> str:
    d = days_since(created_at)
    if reply_count > 5:
        return f"🔥 Aktif tartışma ({reply_count} yanıt)"
    if d <= 3:
        return "🆕 Yeni paylaşım"
    return "💬 Topluluk"


# ─── Eski endpoint (geriye uyumlu) ────────────────────
@router.get("")
async def get_recommendations_compat(request: Request, limit: int = 10):
    """Geriye uyumluluk — düz liste (tüm section'lar birleşik)."""
    flow = await get_flow(request=request)
    all_items = []
    for section in flow["sections"].values():
        all_items.extend(section)
    # Score DESC, tie-break ID ASC
    all_items.sort(key=lambda x: (-x.get("score", 0), x.get("id", 0)))
    return {
        "data": all_items[:limit],
        "context": flow["context"],
    }