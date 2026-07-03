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


# ─── User Context builder ─────────────────────────────
async def _build_user_context(user_id: str) -> UserContext:
    """Kullanıcının attempt'lerinden bağlam çıkar.

    Son çözdüğü soruları (id, title, category) çek — personal section reason'ları için.
    """
    sb = get_supabase_admin()
    ctx = UserContext(is_authenticated=True)

    try:
        attempts_res = (
            sb.table("interview_attempts")
            .select("question_id, success, passed_tests, total_tests, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )
        attempts = attempts_res.data or []
        if not attempts:
            return ctx

        ctx.solved_ids = list({a["question_id"] for a in attempts if a.get("success")})
        ctx.attempted_ids = list({a["question_id"] for a in attempts})
        ctx.total_attempts = len(attempts)
        ctx.success_rate = sum(1 for a in attempts if a.get("success")) / max(len(attempts), 1)

        # Kategori bilgisi — recent_solved için
        q_ids = list({a["question_id"] for a in attempts})
        try:
            q_res = sb.table("interwiews").select("id, title, category").in_("id", q_ids).execute()
            q_map = {r["id"]: r for r in (q_res.data or [])}
        except Exception:
            q_map = {}

        # solved_categories (unique)
        solved_cats = []
        for qid in ctx.solved_ids:
            q = q_map.get(qid)
            if q and q.get("category") and q["category"] not in solved_cats:
                solved_cats.append(q["category"])
        ctx.solved_categories = solved_cats

        # recent_solved: son başarılı denemelerden, soru başlığı ile birlikte
        recent_solved_seen = set()
        for a in attempts:
            if a.get("success"):
                qid = a["question_id"]
                if qid in recent_solved_seen:
                    continue
                recent_solved_seen.add(qid)
                q = q_map.get(qid)
                if q:
                    ctx.recent_solved.append((
                        qid,
                        q.get("title") or "",
                        q.get("category") or "",
                    ))
                if len(ctx.recent_solved) >= 10:
                    break

    except Exception:
        pass
    return ctx


# ─── Tüm soruları DB'den çek ─────────────────────────
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
    """4 section'lı kişiselleştirilmiş akış.

    Sections:
    - personal: Kullanıcının çözdüğü soruların kategorilerinden benzer sorular
    - popular: attempt_count en yüksek 5 soru
    - recent: created_at en yeni 5 soru
    - next_level: başarı oranına göre bir üst seviye soruları

    Deterministik: aynı (user, db_state) → aynı sonuç.
    Misafir: personal section beginner sorularla dolar.
    """
    user_ctx = UserContext(is_authenticated=False)
    try:
        user = await get_current_user(request)
        user_ctx = await _build_user_context(user["id"])
    except HTTPException:
        pass

    questions = _fetch_all_questions()
    sections, ctx_dict = build_flow(questions, user_ctx)

    return {
        "sections": to_api_dict(sections),
        "context": ctx_dict,
    }


# ─── Endpoint: Topluluk ────────────────────────────────
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


# ─── Eski endpoint (geriye uyumlu) ───────────────────
@router.get("")
async def get_recommendations_compat(request: Request, limit: int = 10):
    """Geriye uyumluluk — düz liste (tüm section'lar birleşik)."""
    flow = await get_flow(request=request)
    all_items = []
    for section in flow["sections"].values():
        all_items.extend(section)
    # ID ASC tie-break
    all_items.sort(key=lambda x: (x.get("section", ""), x.get("id", 0)))
    return {
        "data": all_items[:limit],
        "context": flow["context"],
    }