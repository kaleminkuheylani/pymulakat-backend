# backend/services/recommendation_engine.py
# Basit, deterministik akış motoru — kişisel ML yok, sadece DB sorguları.
#
# 4 Section:
#   1) Senin İçin Seçtiklerimiz    → kullanıcının çözdüğü soruların kategorilerinden
#   2) En Çok Çözülenler          → attempt_count DESC
#   3) Yeni Eklenenler             → created_at DESC
#   4) Bir Sonraki Seviye          → kullanıcının başarı oranına göre zıt seviye
#
# Deterministik: aynı (user, db_state) → aynı sonuç. Tie-break: id ASC.

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# ─── Slug fallback (DB'de slug NULL olsa da URL üret) ──
_TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def slugify(text: str) -> str:
    if not text:
        return ""
    s = text.translate(_TR_MAP).lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or ""


# ─── Veri modelleri ──────────────────────────────────────
@dataclass(frozen=True)
class QuestionLite:
    id: int
    title: str
    category: str
    level: str  # beginner | intermediate | advanced
    slug: str = ""
    view_count: int = 0
    attempt_count: int = 0
    created_at: str = ""


@dataclass
class UserContext:
    is_authenticated: bool = False
    solved_ids: List[int] = field(default_factory=list)
    attempted_ids: List[int] = field(default_factory=list)
    # Kullanıcının çözdüğü soruların kategorileri (unique)
    solved_categories: List[str] = field(default_factory=list)
    # Kullanıcının seviyesi (success_rate'e göre)
    success_rate: float = 0.0
    total_attempts: int = 0
    # Kullanıcının son çözdüğü sorular (id + title + category) — collaborative filtering reason için
    recent_solved: List[Tuple[int, str, str]] = field(default_factory=list)  # (id, title, category)


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


# ─── Tarih yardımcıları ──────────────────────────────────
def days_since(iso_str: str) -> float:
    if not iso_str:
        return 9999.0
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", ""))
        return (datetime.utcnow() - dt).total_seconds() / 86400
    except Exception:
        return 9999.0


# ─── Section sabitleri ───────────────────────────────────
SECTION_LIMITS = {
    "personal": 5,    # Senin İçin
    "popular": 5,     # En Çok Çözülenler
    "recent": 5,      # Yeni Eklenenler
    "next_level": 5,  # Bir Sonraki Seviye
}


# ─── Level atama (success_rate → hedef level) ──────────
LEVEL_ORDER = ["beginner", "intermediate", "advanced"]


def infer_current_level(success_rate: float) -> str:
    """Kullanıcının mevcut seviyesi."""
    if success_rate >= 0.7:
        return "advanced"
    if success_rate >= 0.3:
        return "intermediate"
    return "beginner"


# ─── Spesifik, sabit reason template'leri ────────────────
def reason_personal(q: QuestionLite, ctx: UserContext) -> str:
    """Collaborative filtering tarzı sebep:
    Kullanıcının son çözdüğü X sorusuna dayanarak 'X'i çözdüğün için Y'yi de çöz'.
    """
    qid = q.id
    cat = q.category

    # Misafir veya henüz hiç çözülmemiş: generic fallback
    if not ctx.is_authenticated or not ctx.recent_solved:
        if ctx.solved_categories:
            return f"#{qid} {cat} — daha önce bu kategoride çözdüğün sorulara benzer"
        return f"#{qid} {cat} — başlangıç için ideal"

    # Kullanıcının son çözdüğü X'i bul: aynı kategoride olan
    # recent_solved en yeni çözülenlerden eskiye sıralı (router tarafında)
    same_cat_solved = [
        (rid, title, c) for (rid, title, c) in ctx.recent_solved
        if c == cat and rid != qid
    ]
    if same_cat_solved:
        rid, title, _ = same_cat_solved[0]
        # Title çok uzunsa kırp
        short_title = (title[:35] + "…") if len(title) > 35 else title
        return f"#{qid} {cat} — #{rid} \"{short_title}\" sorusunu çözdüğün için benzer"

    # Aynı kategoride yoksa: son çözdüğü herhangi bir X'i referans al
    rid, title, c = ctx.recent_solved[0]
    short_title = (title[:35] + "…") if len(title) > 35 else title
    if c != cat:
        return f"#{qid} {cat} — #{rid} \"{short_title}\" çözdükten sonra yeni kategoriye geç"
    return f"#{qid} {cat} — #{rid} \"{short_title}\" sorusundan sonra"


def reason_popular(q: QuestionLite) -> str:
    a = q.attempt_count or 0
    v = q.view_count or 0
    if a >= 50:
        return f"#{q.id} — {a} kişi çözdü, mülakat klasikleri arasında"
    if a >= 10:
        return f"#{q.id} — {a} deneme yapıldı"
    if v >= 100:
        return f"#{q.id} — {v} kez görüntülendi"
    return f"#{q.id} — platformda öne çıkan sorulardan"


def reason_recent(q: QuestionLite) -> str:
    d = days_since(q.created_at)
    if d < 1:
        return f"#{q.id} — bugün eklendi"
    if d < 7:
        return f"#{q.id} — bu hafta eklendi"
    if d < 30:
        return f"#{q.id} — bu ay eklendi"
    return f"#{q.id} — yakın zamanda eklendi"


def reason_next_level(q: QuestionLite, current_level: str, target_level: str, ctx: UserContext) -> str:
    qid = q.id
    success_pct = int(ctx.success_rate * 100)
    if target_level != current_level:
        return f"#{qid} {target_level} — başarı oranın %{success_pct}, seviye atlamaya hazırsın"
    # target == current: kullanıcı üst seviyeye henüz hazır değil, mevcut seviyede pratik
    return f"#{qid} {current_level} — başarı oranın %{success_pct}, mevcut seviyede biraz daha pratik"


# ─── ANA MOTOR ───────────────────────────────────────────
def build_flow(
    questions: List[QuestionLite],
    ctx: UserContext,
) -> Tuple[Dict[str, List[FlowItem]], Dict]:
    """4 section'lı deterministik akış üret."""

    # ── 1) Senin İçin Seçtiklerimiz ──
    # Kullanıcının çözdüğü kategorilerden, henüz çözmediği sorular
    solved_set = set(ctx.solved_ids)
    personal_pool: List[QuestionLite] = []
    if ctx.solved_categories:
        # Çözülmüş kategorilerden, henüz çözülmemiş
        personal_pool = [
            q for q in questions
            if q.id not in solved_set
            and q.category in ctx.solved_categories
        ]
        # Yeterli değilse çözülmemiş sorulardan ekle (en yeni ID'lerden — DB'nin yeni ekledikleri)
        if len(personal_pool) < SECTION_LIMITS["personal"]:
            extra = [
                q for q in questions
                if q.id not in solved_set
                and q.category not in ctx.solved_categories
            ]
            personal_pool.extend(extra)
        # Tie-break: aynı kategori içinde küçük ID'ler önce (deterministik)
        personal_pool = sorted(personal_pool, key=lambda q: (
            ctx.solved_categories.index(q.category) if q.category in ctx.solved_categories else 99,
            q.id,
        ))[:SECTION_LIMITS["personal"]]
    else:
        # Misafir veya hiç çözülmemiş: en temel beginner sorulardan
        personal_pool = sorted(
            [q for q in questions if q.level == "beginner"],
            key=lambda q: q.id,
        )[:SECTION_LIMITS["personal"]]

    personal_items = [
        FlowItem(
            type="question",
            id=q.id, title=q.title, slug=q.slug or slugify(q.title),
            category=q.category, level=q.level,
            section="personal",
            reason=reason_personal(q, ctx),
            view_count=q.view_count, attempt_count=q.attempt_count,
        )
        for q in personal_pool
    ]

    # ── 2) En Çok Çözülenler ──
    popular_pool = sorted(
        questions,
        key=lambda q: (-(q.attempt_count or 0), q.id),
    )[:SECTION_LIMITS["popular"]]

    popular_items = [
        FlowItem(
            type="question",
            id=q.id, title=q.title, slug=q.slug or slugify(q.title),
            category=q.category, level=q.level,
            section="popular",
            reason=reason_popular(q),
            view_count=q.view_count, attempt_count=q.attempt_count,
        )
        for q in popular_pool
    ]

    # ── 3) Yeni Eklenenler ──
    def effective_date(q: QuestionLite) -> float:
        if q.created_at:
            try:
                return datetime.fromisoformat(q.created_at.replace("Z", "")).timestamp()
            except Exception:
                pass
        # DB created_at yoksa: max_id bazlı fallback
        max_id = max((qq.id for qq in questions), default=88)
        return (max_id - q.id) * 86400

    recent_pool = sorted(questions, key=lambda q: -effective_date(q))[:SECTION_LIMITS["recent"]]

    recent_items = [
        FlowItem(
            type="question",
            id=q.id, title=q.title, slug=q.slug or slugify(q.title),
            category=q.category, level=q.level,
            section="recent",
            reason=reason_recent(q),
            view_count=q.view_count, attempt_count=q.attempt_count,
        )
        for q in recent_pool
    ]

    # ── 4) Bir Sonraki Seviye ──
    current_level = infer_current_level(ctx.success_rate)
    current_idx = LEVEL_ORDER.index(current_level) if current_level in LEVEL_ORDER else 0
    target_idx = min(current_idx + 1, len(LEVEL_ORDER) - 1)
    target_level = LEVEL_ORDER[target_idx]

    # Hedef seviyede, henüz çözülmemiş sorular
    next_pool = [
        q for q in questions
        if q.id not in solved_set and q.level == target_level
    ]
    # Hedef seviyede yoksa: mevcut seviyede, çözülmemiş sorular (pratik)
    if not next_pool:
        next_pool = [q for q in questions if q.id not in solved_set and q.level == current_level]

    # Tie-break: küçük ID önce (deterministik)
    next_pool = sorted(next_pool, key=lambda q: q.id)[:SECTION_LIMITS["next_level"]]

    next_items = [
        FlowItem(
            type="question",
            id=q.id, title=q.title, slug=q.slug or slugify(q.title),
            category=q.category, level=q.level,
            section="next_level",
            reason=reason_next_level(q, current_level, target_level, ctx),
            view_count=q.view_count, attempt_count=q.attempt_count,
        )
        for q in next_pool
    ]

    # ── 5) Dedupe: aynı soru 2 section'da olmasın ──
    seen: set = set()
    final: Dict[str, List[FlowItem]] = {
        "personal": [],
        "popular": [],
        "recent": [],
        "next_level": [],
    }
    priority = ["personal", "next_level", "recent", "popular"]
    src_map = {
        "personal": personal_items,
        "next_level": next_items,
        "recent": recent_items,
        "popular": popular_items,
    }
    for sec in priority:
        for it in src_map[sec]:
            if it.id in seen:
                continue
            seen.add(it.id)
            final[sec].append(it)

    # ── 6) Context ──
    flow_context = {
        "is_authenticated": ctx.is_authenticated,
        "solved_categories": ctx.solved_categories,
        "success_rate": round(ctx.success_rate, 2),
        "total_attempts": ctx.total_attempts,
        "current_level": current_level,
        "target_level": target_level,
        "total_items": sum(len(v) for v in final.values()),
    }

    return final, flow_context


# ─── Dict dönüşümü (FastAPI için) ──────────────────────
def to_api_dict(sections: Dict[str, List[FlowItem]]) -> Dict[str, List[Dict]]:
    return {
        sec: [
            {
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
            for it in items
        ]
        for sec, items in sections.items()
    }