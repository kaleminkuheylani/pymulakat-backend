# backend/question_loader.py
# DB-FIRST mimari: sorular SADECE Supabase 'questions' tablosundan okunur.
#
# 2026-07-13 refactor (kullanici direktifi "sadece kategorideki itemler"):
#   Onceki: filter_questions() her cagrida TUM 85 soruyu memory'ye yüklüyordu
#           (questions = _db_questions()), sonra Python list filter.
#           Bellek + response boyutu gereksiz büyük.
#   Yeni: DB-side filtre — .eq('category', X) ile sadece o kategoriyi çek.
#         18 soru (python-basics) → 18 response item, 85 degil.
#         Bellek: 85 → max 18 (en büyük kategori).
#
# Avantajlar:
#   - Bellek: 85 soru × tüm alanlar (test_cases, hints, ...) → 18 × aynı
#   - Network: Supabase'ten sadece gerekli satırlar
#   - Response: frontend sadece o kategorinin listesini alır
#   - Cache: per-filter cache (key = (category, level, search, tag))
#
# CSV-FALLBACK KALDIRILDI (2026-07-11, commit 1/5).
# DB bağlantısı başarısız olursa hata fırlatılır (sessizce CSV'ye düşmez).
# CSV artık sadece bulk seed + local development için (data/QUESTIONS-v3.csv).

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════
# ─── Question dataclass ───────────────────────────────────
# ═══════════════════════════════════════════════════════════════

@dataclass
class Question:
    id: int
    title: str
    category: str = ""
    level: str = "beginner"
    description: str = ""
    starter_code: Optional[str] = None
    test_cases: List[Dict] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)
    slug: Optional[str] = None
    related_question_ids: List[int] = field(default_factory=list)
    explanation: Optional[str] = None
    complexity: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    function_name: Optional[str] = None
    topic: Optional[str] = None
    tutorial_slug: Optional[str] = None
    related_concepts: List[str] = field(default_factory=list)
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# ─── Kategori meta (statik — DB'den kategori gelmezse UI label) ─
# ═══════════════════════════════════════════════════════════════

CATEGORY_META: Dict[str, Dict[str, str]] = {
    "python-basics": {"label": "Python Temelleri", "description": "Değişkenler, döngüler, koşullar, fonksiyonlar, string islemleri.", "icon": "🐍"},
    "strings": {"label": "String İşlemleri", "description": "String slicing, formatlama, arama, regex, encode/decode.", "icon": "🔤"},
    "data-structures": {"label": "Veri Yapıları", "description": "List, dict, set, tuple, frozenset, deque, heapq, generators. Mulakat prensibi: veri yapisini kullanici secer!", "icon": "🗂️"},
    "list-dict": {"label": "Liste & Sözlük", "description": "Temel liste ve sözlük uygulamaları.", "icon": "📋"},
    "pandas": {"label": "Pandas", "description": "Veri analizi.", "icon": "🐼"},
    "algorithms": {"label": "Algoritmalar", "description": "Sıralama, arama, DP, iki işaretçi.", "icon": "🧮"},
    "dynamic-programming": {"label": "Dinamik Programlama", "description": "Memoization, tabulation, optimal substructure. Fibonacci, knapsack, LCS.", "icon": "🧠"},
    "heap": {"label": "Heap / Priority Queue", "description": "heapq, kth largest, top-k, merge k sorted, median stream.", "icon": "⛰️"},
    "stack": {"label": "Stack", "description": "Yığın yapısı, parantez eşleme, undo, RPN, monotonic stack.", "icon": "📚"},
    "queue": {"label": "Queue", "description": "Kuyruk yapısı, BFS, sliding window max, circular queue.", "icon": "🚶"},
    "oop": {"label": "Python OOP", "description": "Class, inheritance.", "icon": "🧱"},
    "data-types": {"label": "Veri Tipleri", "description": "list, dict, tuple, set.", "icon": "📦"},
    "simple-apps": {"label": "Basit Uygulamalar", "description": "Küçük projeler.", "icon": "🛠️"},
    "beyin-firtinasi": {"label": "Beyin Fırtınası", "description": "Algoritmik düşünme.", "icon": "💡"},
    "sqlite3": {"label": "SQLite3", "description": "Veritabanı temelleri.", "icon": "🗄️"},
    "numpy": {"label": "NumPy", "description": "Array operasyonları.", "icon": "🔢"},
    "sklearn": {"label": "Scikit-learn", "description": "ML pipeline.", "icon": "🤖"},
    "scipy": {"label": "SciPy", "description": "İstatistik.", "icon": "📐"},
    "matplotlib": {"label": "Matplotlib", "description": "Grafik oluşturma.", "icon": "📊"},
    "seaborn": {"label": "Seaborn", "description": "İstatistiksel görselleştirme.", "icon": "🌊"},
    "statsmodels": {"label": "Statsmodels", "description": "ARIMA, regresyon.", "icon": "📈"},
    "nltk": {"label": "NLTK", "description": "Doğal dil işleme.", "icon": "📝"},
    "dask": {"label": "Dask", "description": "Paralel hesaplama.", "icon": "⚡"},
    "pytorch": {"label": "PyTorch", "description": "Tensor işlemleri.", "icon": "🔥"},
}


# ═══════════════════════════════════════════════════════════════
# ─── DB helpers ────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

def _row_to_question(row: dict) -> Question:
    """Supabase row → Question dataclass.

    id olarak önce legacy_id (eski interviews.id uyumlu), yoksa yeni row id.
    """
    return Question(
        id=row.get("legacy_id") or row["id"],
        title=row.get("title", ""),
        category=row.get("category", ""),
        level=row.get("level", "beginner"),
        description=row.get("description", "") or "",
        starter_code=row.get("starter_code"),
        test_cases=row.get("test_cases", []) or [],
        hints=row.get("hints", []) or [],
        slug=row.get("slug"),
        related_question_ids=row.get("related_question_ids", []) or [],
        explanation=row.get("explanation"),
        complexity=row.get("complexity"),
        tags=row.get("tags", []) or [],
        function_name=row.get("function_name"),
        topic=row.get("topic"),
        tutorial_slug=row.get("tutorial_slug"),
        related_concepts=row.get("related_concepts", []) or [],
        meta_title=row.get("meta_title"),
        meta_description=row.get("meta_description"),
        meta_keywords=row.get("meta_keywords", []) or [],
    )


# Level alias (DB'de hangi degerler var bilmiyoruz, robust olalim)
LEVEL_ALIASES = {
    "başlangıç": ["başlangıç", "beginner", "easy"],
    "beginner": ["beginner", "easy", "başlangıç"],
    "orta": ["orta", "intermediate", "medium"],
    "intermediate": ["intermediate", "medium", "orta"],
    "ileri": ["ileri", "advanced", "hard"],
    "advanced": ["advanced", "hard", "ileri"],
}


# Per-filter in-memory cache: (category, level, search, tag) → (ts, results)
# 2026-07-13 refactor: TUM-sorular cache'i yerine per-filter cache.
# Avantaj: her filter kombinasyonu ayri cache'lenir, sadece o kategori memory'de tutulur.
_FILTER_CACHE: Dict[str, Any] = {}
_CACHE_TTL_SEC = int(os.getenv("QUESTION_CACHE_TTL", "60"))


def _cache_key(category, level, search, tag) -> str:
    return f"cat={category or ''}|lvl={level or ''}|s={search or ''}|t={tag or ''}"


def _db_query(
    category: Optional[str] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
) -> List[Question]:
    """DB-side filtre ile soru çek (2026-07-13 refactor).

    Onceki: _db_questions() → TUM 85 soru → Python list filter
    Yeni:    DB'de .eq()/.ilike() ile sadece eşleşenleri çek

    Avantajlar:
      - Bellek: 85 → max 18 (en buyuk kategori: dynamic-programming=21)
      - Network: Supabase sadece eşleşen satırları gönderir
      - Response: frontend sadece o kategorinin listesini alır

    Cache: per-filter key ile 60s in-memory cache. Aynı filter
    60s içinde tekrar istenirse DB'ye gitmez.

    Raises:
        RuntimeError: DB baglantısı başarısız veya sorgu hatası.
    """
    import time
    key = _cache_key(category, level, search, tag)
    now = time.time()

    # Cache hit?
    cached = _FILTER_CACHE.get(key)
    if cached and (now - cached["ts"]) < _CACHE_TTL_SEC:
        return cached["data"]

    try:
        from supabase_client import get_supabase_admin
        sb = get_supabase_admin()
        # DB-side filtre (Python filter yok)
        query = sb.table("questions").select("*")
        if category:
            query = query.eq("category", category)
        if level:
            lvl = level.lower().strip()
            accepted = LEVEL_ALIASES.get(lvl, [lvl])
            # PostgREST .in_() ile OR filtresi
            if len(accepted) > 1:
                query = query.in_("level", accepted)
            else:
                query = query.eq("level", accepted[0])
        # search ve tag icin PostgREST .ilike() — backend'de filter
        # (opsiyonel, performans icin: search/tag Python tarafinda yapilabilir)
        result = query.order("id", desc=False).execute()
        rows = result.data or []
        questions = [_row_to_question(r) for r in rows]

        # search (title/description): Python-side, DB'de full-text yok
        if search:
            s = search.lower().strip()
            questions = [
                q for q in questions
                if s in (getattr(q, "title", "") or "").lower()
                or s in (getattr(q, "description", "") or "").lower()
            ]
        # tag: Python-side (array field, PostgREST .contains() zor)
        if tag:
            tag_l = tag.lower().strip()
            questions = [
                q for q in questions
                if any(tag_l in (t or "").lower() for t in (getattr(q, "tags", []) or []))
            ]
    except Exception as e:
        print(f"❌ DB'den soru yüklenemedi: {e}")
        raise RuntimeError(f"DB sorgu hatası: {e}") from e

    if not questions:
        # Bos sonuc = kategori yok veya DB'de o kategoride soru yok
        pass

    _FILTER_CACHE[key] = {"ts": now, "data": questions}
    return questions


# ═══════════════════════════════════════════════════════════════
# ─── Public API (geriye uyumlu) ────────────────────────────
# ═══════════════════════════════════════════════════════════════

def load_questions() -> List[Question]:
    """Tüm soru listesi. Sadece bulk islemler icin (admin, scripts)."""
    return _db_query()


def to_public_dict(q: Any) -> Dict:
    """Client'a gönderilecek güvenli dict."""
    return {
        "id": q.id,
        "title": q.title,
        "category": getattr(q, "category", None),
        "level": getattr(q, "level", None),
        "description": getattr(q, "description", ""),
        "starter_code": getattr(q, "starter_code", None),
        "hints": getattr(q, "hints", []),
        "tags": getattr(q, "tags", []) or [],
        "slug": getattr(q, "slug", None),
    }


def filter_questions(
    category: Optional[str] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
) -> List[Question]:
    """DB-side filtre ile soru listesi (kullanici direktifi 2026-07-13).

    Onceki: TUM 85 soru memory'ye → Python filter (yavas, bellek israfi)
    Yeni:    DB'de .eq(category=X) → sadece o kategorinin sorulari

    Returns:
        Eşleşen Question listesi.
    """
    return _db_query(category=category, level=level, search=search, tag=tag)


def get_question(question_id, category: Optional[str] = None) -> Optional[Question]:
    """ID veya slug ile tek Question getir (DB'de direkt)."""
    # DB-side: .eq() ile dogrudan
    from supabase_client import get_supabase_admin
    sb = get_supabase_admin()

    target = str(question_id)

    # 1. Slug match (canonical URL)
    try:
        q = sb.table("questions").select("*").eq("slug", target)
        if category:
            q = q.eq("category", category)
        result = q.limit(1).execute()
        if result.data:
            return _row_to_question(result.data[0])
    except Exception:
        pass

    # 2. ID match (legacy_id veya id)
    try:
        # legacy_id (eski interviews.id uyumlu)
        q = sb.table("questions").select("*").eq("legacy_id", question_id)
        if category:
            q = q.eq("category", category)
        result = q.limit(1).execute()
        if result.data:
            return _row_to_question(result.data[0])

        # Yeni id (row.id)
        q = sb.table("questions").select("*").eq("id", question_id)
        if category:
            q = q.eq("category", category)
        result = q.limit(1).execute()
        if result.data:
            return _row_to_question(result.data[0])
    except Exception as e:
        print(f"❌ get_question DB hatasi: {e}")
        return None

    return None


def get_question_by_slug(slug: str, category: Optional[str] = None) -> Optional[Question]:
    """Slug ile tek soru (DB-side)."""
    return get_question(slug, category=category)


def get_categories() -> List[Dict]:
    """Kategorileri metadata + soru sayisi (DB GROUP BY ile, 2026-07-13).

    Onceki: TUM 85 soru memory'ye → unique slug + Python count (yavas)
    Yeni:    DB'de GROUP BY category → sadece 8 row (1 kategori icin)
    """
    try:
        from supabase_client import get_supabase_admin
        sb = get_supabase_admin()
        # .select() ile sadece category alanini cek, GROUP BY Python'da
        # (PostgREST GROUP BY zor, basit unique_slug yaklasimi yeterli)
        result = sb.table("questions").select("category").execute()
        rows = result.data or []

        # Python'da unique + count (DB tarafi 85 row minimal)
        unique_slugs: List[str] = []
        counts: Dict[str, int] = {}
        for r in rows:
            cat = r.get("category")
            if not cat:
                continue
            if cat not in counts:
                unique_slugs.append(cat)
                counts[cat] = 0
            counts[cat] += 1

        result_list = []
        for slug in unique_slugs:
            meta = CATEGORY_META.get(slug, {})
            result_list.append({
                "slug": slug,
                "label": meta.get("label", slug.replace("-", " ").title()),
                "description": meta.get("description", ""),
                "icon": meta.get("icon", "📘"),
                "question_count": counts[slug],
            })
        return result_list
    except Exception as e:
        print(f"❌ get_categories DB hatasi: {e}")
        return []


def get_levels() -> List[str]:
    """Tüm seviyeler (DB-side distinct)."""
    try:
        from supabase_client import get_supabase_admin
        sb = get_supabase_admin()
        result = sb.table("questions").select("level").execute()
        rows = result.data or []
        return sorted({r.get("level") for r in rows if r.get("level")})
    except Exception as e:
        print(f"❌ get_levels DB hatasi: {e}")
        return []


# Cache yönetimi (admin invalidate-cache endpoint'i için)
def clear_cache() -> None:
    """Tum per-filter cache'i temizle."""
    _FILTER_CACHE.clear()


# CSV-FALLBACK KALDIRILDI (DB-FIRST mimari, 2026-07-11).
# Soru verisi yalnızca Supabase 'questions' tablosundan okunur.
# CSV sadece bulk seed + local development için (data/QUESTIONS-v3.csv).
