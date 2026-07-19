# backend/routers/recommendations.py
# Router -> Recommendation Engine koprusu.
# Kaynak: questions tablosu (DB-FIRST). Eski interwiews KALDIRILDI.

from collections import Counter
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


def _qid(row: dict) -> int:
    """questions satiri -> public id (legacy_id oncelikli)."""
    return int(row.get("legacy_id") or row.get("id") or 0)


async def _build_user_context(user_id: str) -> UserContext:
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

        ctx.solved_ids = list({int(a["question_id"]) for a in attempts if a.get("success") and a.get("question_id") is not None})
        ctx.attempted_ids = list({int(a["question_id"]) for a in attempts if a.get("question_id") is not None})
        ctx.total_attempts = len(attempts)
        ctx.success_rate = sum(1 for a in attempts if a.get("success")) / max(len(attempts), 1)

        q_ids = list({int(a["question_id"]) for a in attempts if a.get("question_id") is not None})
        q_map = {}
        if q_ids:
            try:
                # legacy_id veya id ile esles
                by_legacy = sb.table("questions").select(
                    "id, legacy_id, title, category, slug, level, related_question_ids, related_concepts"
                ).in_("legacy_id", q_ids).execute().data or []
                by_id = sb.table("questions").select(
                    "id, legacy_id, title, category, slug, level, related_question_ids, related_concepts"
                ).in_("id", q_ids).execute().data or []
                for r in by_legacy + by_id:
                    public_id = _qid(r)
                    q_map[public_id] = r
                    # ham id de map'e
                    if r.get("id") is not None:
                        q_map[int(r["id"])] = r
                    if r.get("legacy_id") is not None:
                        q_map[int(r["legacy_id"])] = r
            except Exception:
                q_map = {}

        solved_cats = []
        for qid in ctx.solved_ids:
            q = q_map.get(qid)
            if q and q.get("category") and q["category"] not in solved_cats:
                solved_cats.append(q["category"])
        ctx.solved_categories = solved_cats

        # Weak categories: basarisiz denemelerin yogunlastigi kategoriler
        from collections import Counter
        fail_cat_counter: Counter = Counter()
        for a in attempts:
            if a.get("success") or a.get("question_id") is None:
                continue
            q = q_map.get(int(a["question_id"]))
            if q and q.get("category"):
                fail_cat_counter[q["category"]] += 1
        # En cok basarisiz olunan 3 kategori
        weak_from_fails = [cat for cat, _ in fail_cat_counter.most_common(3)]
        # Cozulmus kategorileri weak'ten cikar
        weak_from_fails = [c for c in weak_from_fails if c not in solved_cats]
        ctx.weak_categories = weak_from_fails

        # Survey: negatif rating → weak sinyali (survey_responses tablosu)
        try:
            survey_res = (
                sb.table("survey_responses")
                .select("rating")
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            if survey_res.data:
                rating = survey_res.data.get("rating", "")
                # Negatif rating'ler → kullanici zorlaniyor, weak categories'i genislet
                if rating in ("questions_weak", "platform_useless", "learning_insufficient"):
                    # Kullanicinin denedigi ama basaramadigi kategorileri onceliklendir
                    if not ctx.weak_categories and ctx.solved_categories:
                        # Hic weak yoksa, cozulen kategorilerin disindakileri ekle
                        pass  # weak_from_fails zaten hesaplandi
        except Exception:
            pass

        recent_solved_seen = set()
        for a in attempts:
            if not a.get("success"):
                continue
            qid = int(a["question_id"])
            if qid in recent_solved_seen:
                continue
            recent_solved_seen.add(qid)
            q = q_map.get(qid)
            if q:
                ctx.recent_solved.append((
                    _qid(q) if q else qid,
                    q.get("title") or "",
                    q.get("category") or "",
                ))
            else:
                ctx.recent_solved.append((qid, "", ""))
            if len(ctx.recent_solved) >= 10:
                break

        # Son denemeler (unique question, en yeni once)
        seen_attempt_q = set()
        for a in attempts:
            qid = a.get("question_id")
            if qid is None:
                continue
            qid = int(qid)
            if qid in seen_attempt_q:
                continue
            seen_attempt_q.add(qid)
            q = q_map.get(qid)
            title = (q or {}).get("title") or f"Soru #{qid}"
            category = (q or {}).get("category") or "programlama-temelleri"
            slug = (q or {}).get("slug") or ""
            level = (q or {}).get("level") or "beginner"
            public_id = _qid(q) if q else qid
            ctx.recent_attempts.append((
                public_id,
                title,
                category,
                slug,
                level,
                bool(a.get("success")),
                a.get("created_at") or "",
                int(a.get("passed_tests") or 0),
                int(a.get("total_tests") or 0),
            ))
            if len(ctx.recent_attempts) >= 12:
                break

    except Exception:
        pass
    return ctx


def _fetch_all_questions() -> list:
    """questions tablosundan QuestionLite listesi + global attempt_count."""
    sb = get_supabase_admin()
    try:
        rows = sb.table("questions").select(
            "id, legacy_id, title, category, level, slug, related_question_ids, related_concepts, created_at"
        ).execute().data or []

        # Global popularity: interview_attempts group by question_id
        attempt_counts: Counter = Counter()
        try:
            # Supabase'te aggregate yoksa ham cek (limit guvenli)
            att = (
                sb.table("interview_attempts")
                .select("question_id")
                .limit(5000)
                .execute()
                .data
                or []
            )
            for a in att:
                if a.get("question_id") is not None:
                    attempt_counts[int(a["question_id"])] += 1
        except Exception:
            pass

        out = []
        for r in rows:
            public_id = _qid(r)
            rel_ids = r.get("related_question_ids") or []
            rel_concepts = r.get("related_concepts") or []
            if not isinstance(rel_ids, list):
                rel_ids = []
            if not isinstance(rel_concepts, list):
                rel_concepts = []
            # attempt_count: legacy_id veya id uzerinden
            ac = attempt_counts.get(public_id, 0)
            if r.get("id") is not None:
                ac = max(ac, attempt_counts.get(int(r["id"]), 0))
            if r.get("legacy_id") is not None:
                ac = max(ac, attempt_counts.get(int(r["legacy_id"]), 0))

            out.append(QuestionLite(
                id=public_id,
                title=r.get("title") or "",
                category=r.get("category") or "programlama-temelleri",
                level=(r.get("level") or "beginner").lower(),
                slug=r.get("slug") or "",
                view_count=0,
                attempt_count=ac,
                created_at=r.get("created_at") or "",
                related_question_ids=tuple(int(x) for x in rel_ids if str(x).lstrip("-").isdigit()),
                related_concepts=tuple(str(x) for x in rel_concepts if x),
            ))
        return out
    except Exception:
        return []


@router.get("/flow")
async def get_flow(request: Request):
    """Kisisellestirilmis akis.

    Sections:
    - personal: yakin konulu / related
    - popular: en cok cozulenler
    - recent: yeni eklenenler
    - recent_attempts: son denemeler
    """
    user_ctx = UserContext(is_authenticated=False)
    try:
        user = await get_current_user(request)
        if user and user.get("id"):
            user_ctx = await _build_user_context(user["id"])
    except HTTPException:
        pass
    except Exception:
        pass

    questions = _fetch_all_questions()
    sections, ctx_dict = build_flow(questions, user_ctx)

    return {
        "sections": to_api_dict(sections),
        "context": ctx_dict,
    }


@router.get("/solved-ids")
async def get_solved_ids(request: Request):
    """Kullanicinin basariyla cozdugu soru id listesi (liste sayfasi rozeti)."""
    try:
        user = await get_current_user(request)
        if not user or not user.get("id"):
            return {"solved_ids": []}
        ctx = await _build_user_context(user["id"])
        return {"solved_ids": ctx.solved_ids}
    except HTTPException:
        return {"solved_ids": []}
    except Exception:
        return {"solved_ids": []}


@router.get("/community")
async def get_community(limit: int = Query(15, le=50)):
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
        return f"Aktif tartisma ({reply_count} yanit)"
    if d <= 3:
        return "Yeni paylasim"
    return "Topluluk"


@router.get("")
async def get_recommendations_compat(request: Request, limit: int = 10):
    flow = await get_flow(request=request)
    all_items = []
    for section in flow["sections"].values():
        all_items.extend(section)
    all_items.sort(key=lambda x: (x.get("section", ""), x.get("id", 0)))
    return {
        "data": all_items[:limit],
        "context": flow["context"],
    }
