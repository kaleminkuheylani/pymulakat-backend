# backend/question_loader.py
# DB-only source of truth.
#
# Sorular SADECE Supabase 'questions' tablosundan okunur.
# Kod içinde veri yok — eklemek/silmek için DB kullan, yoksa seed script'i çalıştır:
#   python scripts/seed_questions.py
#
# API contract aynı: Question dataclass + to_public_dict.

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════
# ─── Question dataclass (sadece tip tanımı, veri yok) ──────
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
    "strings": {"label": "String İşlemleri", "description": "(deprecated — python-basics altinda)", "icon": "🔤"},
    "data-structures": {"label": "Veri Yapıları", "description": "List, dict, set, tuple, frozenset, deque, heapq, generators. Mulakat prensibi: veri yapisini kullanici secer!", "icon": "🗂️"},
    "list-dict": {"label": "Liste & Sözlük", "description": "Temel liste ve sözlük uygulamaları.", "icon": "📋"},
    "pandas": {"label": "Pandas", "description": "Veri analizi.", "icon": "🐼"},
    "algorithms": {"label": "Algoritmalar", "description": "Sıralama, arama, DP, iki işaretçi.", "icon": "🧮"},
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


# In-process cache: aynı request içinde N+1 query önleme
_CACHE: Dict[str, Any] = {"data": None, "ts": 0.0}
_CACHE_TTL_SEC = int(os.getenv("QUESTION_CACHE_TTL", "60"))


def _db_questions() -> List[Question]:
    """Tüm published soruları DB'den çek (60s in-memory cache).

    DB bağlantısı başarısız veya boş dönerse data/QUESTIONS-v3.py fallback kullan.
    Bu sayede deploy/URL hatası olsa bile API yanıt verir.
    """
    import time
    now = time.time()
    if _CACHE["data"] is not None and (now - _CACHE["ts"]) < _CACHE_TTL_SEC:
        return _CACHE["data"]

    # Önce DB'den dene
    db_questions: List[Question] = []
    db_error: Optional[str] = None
    try:
        from supabase_client import get_supabase
        sb = get_supabase()
        result = sb.table("questions").select("*").eq("is_published", True).execute()
        rows = result.data or []
        db_questions = [_row_to_question(r) for r in rows]
        db_questions.sort(key=lambda x: x.id)
    except Exception as e:
        db_error = str(e)
        print(f"⚠️ DB'den soru yüklenemedi: {e}")

    # DB'den veri geldiyse onu kullan
    if db_questions:
        _CACHE["data"] = db_questions
        _CACHE["ts"] = now
        return db_questions

    # DB bağlantısı kurulamadıysa VEYA boş döndüyse fallback'e geç
    if db_error or not db_questions:
        fallback = _load_questions_v3_fallback()
        if fallback:
            print(f"🔄 Fallback: data/QUESTIONS-v3.py'den {len(fallback)} soru yüklendi (db_error={bool(db_error)}, db_empty={not db_questions})")
            _CACHE["data"] = fallback
            _CACHE["ts"] = now
            return fallback

    # Hem DB hem fallback boş
    if _CACHE["data"] is not None:
        return _CACHE["data"]
    return []


def _load_questions_v3_fallback() -> List[Question]:
    """data/QUESTIONS-v3.py'den soru yükle (DB fallback).

    dataclass → DB row dataclass dönüşümü.
    CATEGORY_META'dan label/description/icon al.
    """
    import importlib.util
    from pathlib import Path

    data_path = Path(__file__).resolve().parent / "data" / "QUESTIONS-v3.py"
    if not data_path.exists():
        print(f"⚠️ Fallback dosyası yok: {data_path}")
        return []

    try:
        spec = importlib.util.spec_from_file_location("questions_v3_fallback", data_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:
        print(f"⚠️ Fallback import hatası: {e}")
        return []

    # SEO_CONTENT merge (varsa)
    seo_path = data_path.parent / "SEO_CONTENT.py"
    if seo_path.exists():
        try:
            spec_seo = importlib.util.spec_from_file_location("seo_content_fallback", seo_path)
            seo_mod = importlib.util.module_from_spec(spec_seo)
            spec_seo.loader.exec_module(seo_mod)
            seo_mod.apply_seo_content()
        except Exception:
            pass  # SEO merge başarısız, devam et

    questions_raw = getattr(mod, "QUESTIONS", [])

    # Question dataclass → DB row dict → Question dataclass (loader)
    result: List[Question] = []
    for q in questions_raw:
        # Mevcut loader'ın Question dataclass'ını kullan
        result.append(Question(
            id=q.id,
            title=q.title,
            category=q.category,
            level=q.level,
            description=getattr(q, "description", "") or "",
            starter_code=getattr(q, "starter_code", None),
            test_cases=getattr(q, "test_cases", []) or [],
            hints=getattr(q, "hints", []) or [],
            slug=getattr(q, "slug", None),
            related_question_ids=list(getattr(q, "related_question_ids", []) or []),
            explanation=getattr(q, "explanation", None),
            complexity=getattr(q, "complexity", None),
            tags=list(getattr(q, "tags", []) or []),
            function_name=None,
            topic=None,
            tutorial_slug=getattr(q, "tutorial_slug", None),
            related_concepts=list(getattr(q, "related_concepts", []) or []),
            meta_title=None,
            meta_description=None,
            meta_keywords=[],
        ))

    return result


def invalidate_cache():
    """Cache'i temizle (seed veya admin update sonrası)."""
    _CACHE["data"] = None
    _CACHE["ts"] = 0.0


# ═══════════════════════════════════════════════════════════════
# ─── Public API ────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════

def load_questions() -> List[Question]:
    """Sadece DB'den soru listesi. Veri eklemek için scripts/seed_questions.py kullan."""
    return _db_questions()


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
    questions = _db_questions()
    filtered = questions

    if category:
        filtered = [q for q in filtered if getattr(q, "category", None) == category]

    if level:
        lvl = level.lower().strip()
        LEVEL_ALIASES = {
            "başlangıç": ["başlangıç", "beginner", "easy"],
            "beginner": ["beginner", "easy", "başlangıç"],
            "orta": ["orta", "intermediate", "medium"],
            "intermediate": ["intermediate", "medium", "orta"],
            "ileri": ["ileri", "advanced", "hard"],
            "advanced": ["advanced", "hard", "ileri"],
        }
        accepted = LEVEL_ALIASES.get(lvl, [lvl])
        filtered = [q for q in filtered if (getattr(q, "level", "") or "").lower() in accepted]

    if search:
        s = search.lower().strip()
        filtered = [
            q for q in filtered
            if s in (getattr(q, "title", "") or "").lower()
            or s in (getattr(q, "description", "") or "").lower()
        ]

    if tag:
        tag_l = tag.lower().strip()
        filtered = [
            q for q in filtered
            if any(tag_l in (t or "").lower() for t in (getattr(q, "tags", []) or []))
        ]

    return filtered


def get_question(question_id, category: Optional[str] = None) -> Optional[Question]:
    """ID veya slug ile tek Question getir."""
    questions = _db_questions()
    target = str(question_id)

    # 1. Slug match (canonical URL)
    slug_match = next((q for q in questions if getattr(q, "slug", None) == target), None)
    if slug_match:
        if category is None or getattr(slug_match, "category", None) == category:
            return slug_match

    # 2. ID match (legacy interviews.id uyumlu)
    for q in questions:
        if q.id != question_id:
            continue
        if category is not None and getattr(q, "category", None) != category:
            continue
        return q
    return None


def get_question_by_slug(slug: str, category: Optional[str] = None) -> Optional[Question]:
    questions = _db_questions()
    for q in questions:
        if getattr(q, "slug", None) == slug:
            if category is None or getattr(q, "category", None) == category:
                return q
    return None


def get_categories() -> List[Dict]:
    """Kategorileri metadata + soru sayısı ile döndür."""
    questions = _db_questions()

    unique_slugs = []
    for q in questions:
        cat = getattr(q, "category", None)
        if cat and cat not in unique_slugs:
            unique_slugs.append(cat)

    result = []
    for slug in unique_slugs:
        meta = CATEGORY_META.get(slug, {})
        count = len([q for q in questions if getattr(q, "category", None) == slug])
        result.append({
            "slug": slug,
            "label": meta.get("label", slug.replace("-", " ").title()),
            "description": meta.get("description", ""),
            "icon": meta.get("icon", "📘"),
            "question_count": count,
        })
    return result


def get_levels() -> List[str]:
    questions = _db_questions()
    return sorted({getattr(q, "level", None) for q in questions if getattr(q, "level", None)})