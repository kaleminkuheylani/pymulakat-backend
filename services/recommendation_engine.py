# backend/services/recommendation_engine.py
# Deterministic, content-based recommendation engine.
# Tüm akış tek fonksiyondan geçer: aynı (user, db_state) → aynı sonuç.

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
    function_name: str = ""
    view_count: int = 0
    attempt_count: int = 0
    created_at: str = ""


@dataclass
class UserContext:
    is_authenticated: bool = False
    solved_ids: List[int] = field(default_factory=list)
    attempted_ids: List[int] = field(default_factory=list)
    top_categories: List[str] = field(default_factory=list)
    weak_categories: List[str] = field(default_factory=list)
    success_rate: float = 0.0
    total_attempts: int = 0
    # Son başarısız denemeler — spesifik reason üretmek için
    recent_failed: List[Tuple[int, str]] = field(default_factory=list)  # (qid, title)
    # Hiç ipucu kullanmadan denediği sorular
    no_hint_failed: List[int] = field(default_factory=list)


@dataclass
class FlowItem:
    type: str
    id: int
    title: str
    slug: str
    category: str
    level: str
    section: str
    reason: str  # Spesifik, kullanıcı verisine dayalı
    score: float
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


# ─── Section sınırları (toplam ~6-8 item) ───────────────
SECTION_LIMITS = {
    "personal": 2,    # En spesifik: user'ın tam state'ine göre
    "recent": 2,      # Son eklenenler
    "popular": 2,     # En çok etkileşim alan
    "next_level": 2,  # Bir üst seviyeye hazırlık
}

# ─── Level atama ────────────────────────────────────────
def infer_level(success_rate: float) -> str:
    if success_rate >= 0.7:
        return "advanced"
    if success_rate >= 0.3:
        return "intermediate"
    return "beginner"


# ─── Spesifik reason üreticileri ────────────────────────
def reason_personal(q: QuestionLite, ctx: UserContext) -> str:
    """Kullanıcının state'ine göre EN spesifik reason. Somut sayılar içerir."""
    qid = q.id

    # 1) Daha önce denemiş ama başaramamış → "tekrar dene"
    if qid in ctx.no_hint_failed:
        return f"#{qid} {q.category}'da ipucusuz denedin — ipuçlarıyla tekrar dene"

    if qid in ctx.attempted_ids and qid not in ctx.solved_ids:
        # Hangi kategoride, kaç kez denemiş?
        if q.category in ctx.top_categories:
            return f"#{qid} {q.title} — {q.category} en güçlü kategorin, bir kez daha dene"
        if q.category in ctx.weak_categories:
            return f"#{qid} {q.title} — {q.category} zorlandığın ama %50+ çözdüğün yer"
        return f"#{qid} {q.title} — daha önce denedin ama tamamlayamadın"

    # 2) Kategori eşleşmesi
    if q.category in ctx.top_categories:
        idx = ctx.top_categories.index(q.category)
        if idx == 0:
            return f"#{qid} {q.title} — {q.category} en başarılı kategorin"
        return f"#{qid} {q.title} — {q.category} başarılı olduğun #{idx + 1}. kategori"

    # 3) Zayıf kategori
    if q.category in ctx.weak_categories:
        return f"#{qid} {q.title} — {q.category} zorlandığın, pratik şansı"

    # 4) Misafir veya state yok
    if not ctx.is_authenticated:
        # Misafirin seviyesini bilmiyoruz, soru hangi kategorideyse onu vurgulayalım
        return f"#{qid} {q.category} — öne çıkan sorulardan"

    return f"#{qid} {q.title} — seviyene uygun"


def reason_recent(q: QuestionLite, max_id: int) -> str:
    """Soru ne kadar yeni? Somut bir gösterge ile."""
    if q.created_at:
        d = days_since(q.created_at)
        if d < 1:
            return f"#{q.id} bugün eklendi"
        if d < 7:
            return f"#{q.id} bu hafta eklendi ({int(d)} gün önce)"
        if d < 30:
            return f"#{q.id} bu ay eklendi"
        return f"#{q.id} yakın zamanda eklendi"
    # ID-bazli fallback
    days_equiv = max_id - q.id
    if days_equiv < 7:
        return f"#{q.id} yeni soru"
    return f"#{q.id} — id-bazli yeni"


def reason_popular(q: QuestionLite) -> str:
    """Gerçek etkileşim sayısı + kategori etiketi."""
    v = q.view_count or 0
    a = q.attempt_count or 0
    if a == 0 and v == 0:
        return f"#{q.id} — klasik mülakat sorusu"

    if a > 0 and v > 0:
        # Tahmini başarı oranı yok ama etkileşim var
        if a >= 50:
            return f"#{q.id} {q.category} — {a} deneme, mülakat klasikleri arasında"
        if a >= 10:
            return f"#{q.id} {q.category} — {a} kişi denedi"
        return f"#{q.id} {q.category} — {v} görüntülenme"

    if a > 0:
        return f"#{q.id} {q.category} — {a} deneme"
    return f"#{q.id} {q.category} — {v} görüntülenme"


def reason_next_level(q: QuestionLite, target_level: str, ctx: UserContext) -> str:
    """Bir üst seviyeye hazırlık için somut gerekçe."""
    qid = q.id
    success_pct = int(ctx.success_rate * 100)
    if target_level == q.level:
        if ctx.success_rate >= 0.7:
            return f"#{qid} {q.level} — başarı oranın %{success_pct}, sıradaki seviyeye hazırsın"
        if ctx.success_rate >= 0.3:
            return f"#{qid} {q.level} — başarı oranın %{success_pct}, biraz daha pratikle geçersin"
        return f"#{qid} {q.level} — başarı oranın %{success_pct}, seviye içi pekiştirme"

    # target_level != q.level (fallback durumu)
    return f"#{qid} {q.level} — mevcut seviyende ilerleme için"


# ─── ANA MOTOR ───────────────────────────────────────────
def build_flow(
    questions: List[QuestionLite],
    ctx: UserContext,
) -> Tuple[Dict[str, List[FlowItem]], Dict]:
    """Deterministik akış üret.

    Args:
        questions: Tüm sorular (QuestionLite listesi).
        ctx: Kullanıcı bağlamı (anonim ise sadece is_authenticated=False yeterli).

    Returns:
        (sections dict, context dict)
    """
    # ── 1) Enrich: her soruya slug ve stats ekle ──
    enriched: List[QuestionLite] = []
    for q in questions:
        enriched.append(QuestionLite(
            id=q.id,
            title=q.title,
            category=q.category,
            level=q.level,
            slug=q.slug or slugify(q.title),
            function_name=q.function_name,
            view_count=q.view_count,
            attempt_count=q.attempt_count,
            created_at=q.created_at,
        ))

    # ── 2) Personal: user'ın state'ine EN spesifik 2 öneri ──
    solved_set = set(ctx.solved_ids)
    attempted_set = set(ctx.attempted_ids)
    current_level = infer_level(ctx.success_rate)

    # Skor: çözülmemiş + level eşleşmesi + kategori eşleşmesi
    def personal_score(q: QuestionLite) -> float:
        if q.id in solved_set:
            return -1000.0  # çözülmüşleri tamamen dışla
        s = 0.0
        if q.level == current_level:
            s += 50
        if q.category in ctx.top_categories:
            s += 30 - ctx.top_categories.index(q.category) * 8
        if q.category in ctx.weak_categories:
            s += 25
        if q.id in attempted_set:
            s += 20  # tekrar denemek değerli
        # Tie-break: küçük ID öne çıksın (deterministik)
        s += max(0, 100 - q.id) * 0.001
        return s

    personal_pool = sorted(enriched, key=personal_score, reverse=True)
    personal_pool = [q for q in personal_pool if personal_score(q) > -500][:SECTION_LIMITS["personal"]]

    personal_items = [
        FlowItem(
            type="question",
            id=q.id,
            title=q.title,
            slug=q.slug,
            category=q.category,
            level=q.level,
            section="personal",
            reason=reason_personal(q, ctx),
            score=personal_score(q),
            view_count=q.view_count,
            attempt_count=q.attempt_count,
        )
        for q in personal_pool
    ]

    # ── 3) Recent: gerçek tarih, yoksa ID-bazli ──
    max_id = max((q.id for q in enriched), default=88)

    def effective_date(q: QuestionLite) -> float:
        if q.created_at:
            try:
                return datetime.fromisoformat(q.created_at.replace("Z", "")).timestamp()
            except Exception:
                pass
        # ID-bazli: max_id = bugün, 1 = en eski
        return (max_id - q.id) * 86400

    recent_pool = sorted(enriched, key=effective_date, reverse=True)[:SECTION_LIMITS["recent"]]
    recent_items = [
        FlowItem(
            type="question",
            id=q.id,
            title=q.title,
            slug=q.slug,
            category=q.category,
            level=q.level,
            section="recent",
            reason=reason_recent(q, max_id),
            score=effective_date(q),
            view_count=q.view_count,
            attempt_count=q.attempt_count,
        )
        for q in recent_pool
    ]

    # ── 4) Popular: gerçek etkileşim, yoksa klasik (id 1-15) ──
    pop_with_stats = [q for q in enriched if (q.view_count or 0) + (q.attempt_count or 0) > 0]
    if pop_with_stats:
        pop_pool = sorted(
            pop_with_stats,
            key=lambda q: (q.view_count or 0) + (q.attempt_count or 0) * 2,
            reverse=True,
        )[:SECTION_LIMITS["popular"]]
    else:
        # Klasikler: küçük ID'ler + deterministik
        pop_pool = sorted([q for q in enriched if 1 <= q.id <= 15], key=lambda q: q.id)[:SECTION_LIMITS["popular"]]

    popular_items = [
        FlowItem(
            type="question",
            id=q.id,
            title=q.title,
            slug=q.slug,
            category=q.category,
            level=q.level,
            section="popular",
            reason=reason_popular(q),
            score=float((q.view_count or 0) + (q.attempt_count or 0) * 2),
            view_count=q.view_count,
            attempt_count=q.attempt_count,
        )
        for q in pop_pool
    ]

    # ── 5) Next-level: bir üst seviyeye hazırlık ──
    level_order = ["beginner", "intermediate", "advanced"]
    current_idx = level_order.index(current_level) if current_level in level_order else 0
    target_idx = min(current_idx + 1, len(level_order) - 1)
    target_level = level_order[target_idx]

    next_pool_unsolved = [
        q for q in enriched
        if q.id not in solved_set and q.level == target_level
    ]
    if not next_pool_unsolved:
        # Hedef seviyede yoksa → mevcut seviyede en yüksek skorlular (deterministik)
        next_pool_unsolved = sorted(
            [q for q in enriched if q.id not in solved_set],
            key=lambda q: (-(ctx.top_categories.index(q.category) if q.category in ctx.top_categories else 99), q.id),
        )

    next_pool = next_pool_unsolved[:SECTION_LIMITS["next_level"]]
    next_items = [
        FlowItem(
            type="question",
            id=q.id,
            title=q.title,
            slug=q.slug,
            category=q.category,
            level=q.level,
            section="next_level",
            reason=reason_next_level(q, target_level, ctx),
            score=100.0 - ctx.top_categories.index(q.category) * 10
                if q.category in ctx.top_categories
                else 50.0,
            view_count=q.view_count,
            attempt_count=q.attempt_count,
        )
        for q in next_pool
    ]

    # ── 6) Dedupe: aynı soru 2 section'da olmasın ──
    seen_ids = set()
    final_sections: Dict[str, List[FlowItem]] = {
        "personal": [],
        "recent": [],
        "popular": [],
        "next_level": [],
    }
    priority = ["personal", "next_level", "recent", "popular"]
    for sec in priority:
        for item in (personal_items if sec == "personal"
                     else next_items if sec == "next_level"
                     else recent_items if sec == "recent"
                     else popular_items):
            if item.id in seen_ids:
                continue
            seen_ids.add(item.id)
            final_sections[sec].append(item)

    # ── 7) Context ──
    flow_context = {
        "is_authenticated": ctx.is_authenticated,
        "top_categories": ctx.top_categories,
        "weak_categories": ctx.weak_categories,
        "success_rate": round(ctx.success_rate, 2),
        "total_attempts": ctx.total_attempts,
        "current_level": current_level,
        "target_level": target_level,
        "total_items": sum(len(v) for v in final_sections.values()),
    }

    return final_sections, flow_context


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
                "score": round(it.score, 3),
                "view_count": it.view_count,
                "attempt_count": it.attempt_count,
            }
            for it in items
        ]
        for sec, items in sections.items()
    }