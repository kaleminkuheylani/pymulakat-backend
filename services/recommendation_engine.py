# backend/services/recommendation_engine.py
# Deterministik akis motoru — personal / popular / recent / recent_attempts
#
# Sections:
#   1) personal         -> cozulen sorulara yakin (related_ids + ayni kategori/konsept)
#   2) popular          -> en cok denenen/cozulen
#   3) recent           -> sisteme yeni eklenenler
#   4) recent_attempts  -> kullanicinin son denemeleri
#
# Deterministik: ayni (user, db_state) -> ayni sonuc. Tie-break: id ASC.

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple


_TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def slugify(text: str) -> str:
    if not text:
        return ""
    s = text.translate(_TR_MAP).lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or ""


@dataclass(frozen=True)
class QuestionLite:
    id: int
    title: str
    category: str
    level: str
    slug: str = ""
    view_count: int = 0
    attempt_count: int = 0
    created_at: str = ""
    related_question_ids: Tuple[int, ...] = ()
    related_concepts: Tuple[str, ...] = ()


@dataclass
class UserContext:
    is_authenticated: bool = False
    solved_ids: List[int] = field(default_factory=list)
    attempted_ids: List[int] = field(default_factory=list)
    solved_categories: List[str] = field(default_factory=list)
    # Basarisiz denemelerin yogunlastigi kategoriler (survey + failed attempts)
    weak_categories: List[str] = field(default_factory=list)
    success_rate: float = 0.0
    total_attempts: int = 0
    # (id, title, category) — basarili cozumler (en yeni once)
    recent_solved: List[Tuple[int, str, str]] = field(default_factory=list)
    # Son denemeler (basarili/basarisiz) — dashboard "Son Denemeler"
    # (question_id, title, category, slug, level, success, created_at, passed, total)
    recent_attempts: List[Tuple] = field(default_factory=list)


@dataclass
class FlowItem:
    type: str
    id: int
    title: str
    slug: str
    category: str
    level: str
    section: str
    reason: str
    view_count: int = 0
    attempt_count: int = 0
    success: Optional[bool] = None
    created_at: str = ""
    passed_tests: int = 0
    total_tests: int = 0


def days_since(iso_str: str) -> float:
    if not iso_str:
        return 9999.0
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00").replace("+00:00", ""))
        return (datetime.utcnow() - dt).total_seconds() / 86400
    except Exception:
        return 9999.0


SECTION_LIMITS = {
    "personal": 5,
    "popular": 5,
    "recent": 5,
    "recent_attempts": 8,
}

LEVEL_ORDER = ["beginner", "intermediate", "advanced"]


def infer_current_level(success_rate: float) -> str:
    if success_rate >= 0.7:
        return "advanced"
    if success_rate >= 0.3:
        return "intermediate"
    return "beginner"


def reason_personal(q: QuestionLite, ctx: UserContext, via_related_from: Optional[int] = None) -> str:
    qid = q.id
    cat = q.category
    if via_related_from is not None:
        src = next((t for (rid, t, _) in ctx.recent_solved if rid == via_related_from), None)
        if src:
            short = (src[:35] + "…") if len(src) > 35 else src
            return f"#{qid} — #{via_related_from} \"{short}\" ile yakin konu"
        return f"#{qid} — cozdugun #{via_related_from} sorusuna yakin"

    if cat in ctx.weak_categories:
        return f"#{qid} {cat} — bu kategoride pratik yapman iyi olur"

    if not ctx.is_authenticated or not ctx.recent_solved:
        if ctx.solved_categories:
            return f"#{qid} {cat} — daha once bu kategoride basarili oldugun icin"
        return f"#{qid} {cat} — baslangic icin ideal"

    same_cat = [(rid, title, c) for (rid, title, c) in ctx.recent_solved if c == cat and rid != qid]
    if same_cat:
        rid, title, _ = same_cat[0]
        short = (title[:35] + "…") if len(title) > 35 else title
        return f"#{qid} {cat} — #{rid} \"{short}\" sonrasi benzer"
    rid, title, c = ctx.recent_solved[0]
    short = (title[:35] + "…") if len(title) > 35 else title
    return f"#{qid} {cat} — #{rid} \"{short}\" cozdukten sonra"


def reason_popular(q: QuestionLite) -> str:
    a = q.attempt_count or 0
    v = q.view_count or 0
    if a >= 50:
        return f"#{q.id} — {a} deneme, mulakat klasigi"
    if a >= 10:
        return f"#{q.id} — {a} deneme yapildi"
    if a >= 1:
        return f"#{q.id} — {a} deneme"
    if v >= 100:
        return f"#{q.id} — {v} kez goruntulendi"
    return f"#{q.id} — platformda one cikan"


def reason_recent(q: QuestionLite) -> str:
    d = days_since(q.created_at)
    if d < 1:
        return f"#{q.id} — bugun eklendi"
    if d < 7:
        return f"#{q.id} — bu hafta eklendi"
    if d < 30:
        return f"#{q.id} — bu ay eklendi"
    return f"#{q.id} — yakin zamanda eklendi"


def reason_attempt(success: bool, passed: int, total: int) -> str:
    if success:
        return f"Basarili · {passed}/{total} test"
    if total > 0:
        return f"Denendi · {passed}/{total} test gecti"
    return "Denendi"


def _to_item(q: QuestionLite, section: str, reason: str, **extra) -> FlowItem:
    return FlowItem(
        type="question",
        id=q.id,
        title=q.title,
        slug=q.slug or slugify(q.title),
        category=q.category,
        level=q.level,
        section=section,
        reason=reason,
        view_count=q.view_count,
        attempt_count=q.attempt_count,
        **extra,
    )


def _build_personal(questions: List[QuestionLite], ctx: UserContext, qmap: Dict[int, QuestionLite]) -> List[FlowItem]:
    solved_set = set(ctx.solved_ids)
    limit = SECTION_LIMITS["personal"]
    picked: List[Tuple[QuestionLite, Optional[int]]] = []  # (q, via_related_from)
    seen: Set[int] = set()

    # 1) related_question_ids of recently solved
    for rid, _title, _cat in ctx.recent_solved:
        src = qmap.get(rid)
        if not src:
            continue
        for rel_id in src.related_question_ids:
            if rel_id in solved_set or rel_id in seen:
                continue
            q = qmap.get(rel_id)
            if not q:
                continue
            seen.add(rel_id)
            picked.append((q, rid))
            if len(picked) >= limit:
                break
        if len(picked) >= limit:
            break

    # 2) same category as solved
    if len(picked) < limit and ctx.solved_categories:
        cat_pool = [
            q for q in questions
            if q.id not in solved_set and q.id not in seen and q.category in ctx.solved_categories
        ]
        cat_pool = sorted(
            cat_pool,
            key=lambda q: (
                ctx.solved_categories.index(q.category) if q.category in ctx.solved_categories else 99,
                q.id,
            ),
        )
        for q in cat_pool:
            seen.add(q.id)
            picked.append((q, None))
            if len(picked) >= limit:
                break

    # 3) weak categories (failed attempts + survey signals) — pratik ihtiyaci
    if len(picked) < limit and ctx.weak_categories:
        weak_pool = [
            q for q in questions
            if q.id not in solved_set and q.id not in seen and q.category in ctx.weak_categories
        ]
        weak_pool = sorted(
            weak_pool,
            key=lambda q: (
                ctx.weak_categories.index(q.category) if q.category in ctx.weak_categories else 99,
                q.id,
            ),
        )
        for q in weak_pool:
            seen.add(q.id)
            picked.append((q, None))
            if len(picked) >= limit:
                break

    # 4) shared related_concepts
    if len(picked) < limit and ctx.recent_solved:
        user_concepts: Set[str] = set()
        for rid, _, _ in ctx.recent_solved:
            src = qmap.get(rid)
            if src:
                user_concepts.update(c.lower() for c in src.related_concepts if c)
        if user_concepts:
            concept_pool = []
            for q in questions:
                if q.id in solved_set or q.id in seen:
                    continue
                q_concepts = {c.lower() for c in q.related_concepts if c}
                overlap = len(user_concepts & q_concepts)
                if overlap:
                    concept_pool.append((overlap, q))
            concept_pool.sort(key=lambda x: (-x[0], x[1].id))
            for _, q in concept_pool:
                seen.add(q.id)
                picked.append((q, None))
                if len(picked) >= limit:
                    break

    # 5) cold start: beginner
    if not picked:
        pool = sorted(
            [q for q in questions if q.level in ("beginner", "başlangıç", "easy") or not q.level],
            key=lambda q: q.id,
        )[:limit]
        if not pool:
            pool = sorted(questions, key=lambda q: q.id)[:limit]
        picked = [(q, None) for q in pool]

    return [
        _to_item(q, "personal", reason_personal(q, ctx, via))
        for q, via in picked[:limit]
    ]


def build_flow(
    questions: List[QuestionLite],
    ctx: UserContext,
) -> Tuple[Dict[str, List[FlowItem]], Dict]:
    qmap = {q.id: q for q in questions}
    solved_set = set(ctx.solved_ids)

    personal_items = _build_personal(questions, ctx, qmap)

    # Popular
    popular_pool = sorted(
        questions,
        key=lambda q: (-(q.attempt_count or 0), -(q.view_count or 0), q.id),
    )[: SECTION_LIMITS["popular"]]
    popular_items = [_to_item(q, "popular", reason_popular(q)) for q in popular_pool]

    # Recent (new on platform)
    def effective_date(q: QuestionLite) -> float:
        if q.created_at:
            try:
                return datetime.fromisoformat(q.created_at.replace("Z", "")).timestamp()
            except Exception:
                pass
        return float(q.id)

    recent_pool = sorted(questions, key=lambda q: -effective_date(q))[: SECTION_LIMITS["recent"]]
    recent_items = [_to_item(q, "recent", reason_recent(q)) for q in recent_pool]

    # Recent attempts (user activity)
    recent_attempt_items: List[FlowItem] = []
    for row in ctx.recent_attempts[: SECTION_LIMITS["recent_attempts"]]:
        # tuple: qid, title, category, slug, level, success, created_at, passed, total
        qid, title, category, slug, level, success, created_at, passed, total = row
        q = qmap.get(int(qid))
        recent_attempt_items.append(
            FlowItem(
                type="question",
                id=int(qid),
                title=title or (q.title if q else f"Soru #{qid}"),
                slug=slug or (q.slug if q else "") or slugify(title or f"soru-{qid}"),
                category=category or (q.category if q else "programlama-temelleri"),
                level=level or (q.level if q else "beginner"),
                section="recent_attempts",
                reason=reason_attempt(bool(success), int(passed or 0), int(total or 0)),
                view_count=q.view_count if q else 0,
                attempt_count=q.attempt_count if q else 0,
                success=bool(success),
                created_at=created_at or "",
                passed_tests=int(passed or 0),
                total_tests=int(total or 0),
            )
        )

    # Dedupe across personal/popular/recent (attempts keep own list)
    seen: Set[int] = set()
    final: Dict[str, List[FlowItem]] = {
        "personal": [],
        "popular": [],
        "recent": [],
        "recent_attempts": recent_attempt_items,
    }
    for sec, items in (
        ("personal", personal_items),
        ("recent", recent_items),
        ("popular", popular_items),
    ):
        for it in items:
            if it.id in seen:
                continue
            seen.add(it.id)
            final[sec].append(it)

    current_level = infer_current_level(ctx.success_rate)
    flow_context = {
        "is_authenticated": ctx.is_authenticated,
        "solved_categories": ctx.solved_categories,
        "solved_ids": list(solved_set),
        "weak_categories": ctx.weak_categories,
        "success_rate": round(ctx.success_rate, 2),
        "total_attempts": ctx.total_attempts,
        "current_level": current_level,
        "target_level": current_level,
        "total_items": sum(len(v) for v in final.values()),
    }
    return final, flow_context


def to_api_dict(sections: Dict[str, List[FlowItem]]) -> Dict[str, List[Dict]]:
    out: Dict[str, List[Dict]] = {}
    for sec, items in sections.items():
        out[sec] = []
        for it in items:
            row = {
                "type": it.type,
                "id": it.id,
                "title": it.title,
                "slug": it.slug,
                "category": it.category,
                "level": it.level,
                "section": it.section,
                "reason": it.reason,
                "view_count": it.view_count,
                "attempt_count": it.attempt_count,
            }
            if it.success is not None:
                row["success"] = it.success
            if it.created_at:
                row["created_at"] = it.created_at
            if it.total_tests:
                row["passed_tests"] = it.passed_tests
                row["total_tests"] = it.total_tests
            out[sec].append(row)
    return out
