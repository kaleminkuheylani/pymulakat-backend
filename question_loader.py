# backend/question_loader.py
# DB-first + QUESTIONS.py fallback mimarisi
#
# Akış:
#   1. load_questions() → Supabase 'questions' tablosunu dene
#   2. DB'de soru varsa ve hata yoksa → DB'den dön
#   3. DB boş/hata → QUESTIONS.py fallback
#
# Frontend aynı Question dataclass'ını alır, API contract değişmez.

import os
from typing import Optional, List, Dict, Any
from data.QUESTIONS import QUESTIONS, Question

# v3 fallback (daha zengin: SEO_CONTENT zenginlestirilmis 70 soru)
# Dynamic import: QUESTIONS-v3.py dosya adi dash (-) iceriyor
import importlib.util as _importlib_util
import os as _os
QUESTIONS_V3 = QUESTIONS  # Fallback degisken
try:
    _v3_path = _os.path.join(_os.path.dirname(__file__), "data", "QUESTIONS-v3.py")
    if _os.path.exists(_v3_path):
        _spec = _importlib_util.spec_from_file_location("data_questions_v3_dynamic", _v3_path)
        _v3_mod = _importlib_util.module_from_spec(_spec)
        _spec.loader.exec_module(_v3_mod)
        QUESTIONS_V3 = _v3_mod.QUESTIONS
except Exception as _e:
    print(f"⚠️ QUESTIONS-v3 fallback yuklenemedi: {_e}")


# ═══════════════════════════════════════════════════════════════
# Kategori meta (DB'den gelirse de fallback olarak kullanılır)
# ═══════════════════════════════════════════════════════════════
CATEGORY_META = {
    "python-basics": {"label": "Python Temelleri", "description": "Değişkenler, döngüler, koşullar, fonksiyonlar.", "icon": "🐍"},
    "strings": {"label": "String İşlemleri", "description": "Metin işleme, slicing, formatlama.", "icon": "🔤"},
    "list-dict": {"label": "Liste & Sözlük", "description": "Veri yapıları.", "icon": "📋"},
    "pandas": {"label": "Pandas", "description": "Veri analizi.", "icon": "🐼"},
    "algorithms": {"label": "Algoritmalar", "description": "Sıralama, arama, DP.", "icon": "🧮"},
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


def _db_row_to_question(row: dict) -> Question:
    """Supabase questions row -> Question dataclass."""
    return Question(
        id=row.get("source_id") or row["id"],
        title=row["title"],
        category=row["category"],
        level=row.get("level", "beginner"),
        description=row.get("description", ""),
        starter_code=row.get("starter_code"),
        test_cases=row.get("test_cases", []) or [],
        hints=row.get("hints", []) or [],
        slug=row.get("slug"),
        related_question_ids=row.get("related_question_ids", []) or [],
        explanation=row.get("explanation"),
        complexity=row.get("complexity"),
        tags=row.get("tags", []) or [],
    )


def _load_from_db() -> Optional[List[Question]]:
    """Supabase 'questions' tablosundan yükle. Hata durumunda None döndür."""
    try:
        from supabase_client import get_supabase
        supabase = get_supabase()
        # Pagination: supabase default 1000 limit, biz 500 yeterli
        response = supabase.table("questions").select("*").eq("is_published", True).execute()
        if response.data and len(response.data) > 0:
            questions = [_db_row_to_question(row) for row in response.data]
            return sorted(questions, key=lambda x: x.id)
        return None  # DB boş, fallback'e düş
    except Exception as e:
        print(f"⚠️ DB'den soru yüklenemedi, QUESTIONS.py fallback kullanılacak: {e}")
        return None


def load_questions() -> List[Question]:
    """DB-first, fallback olarak QUESTIONS-v3.py (zenginlestirilmis)."""
    db_loaded = _load_from_db()
    if db_loaded is not None:
        return db_loaded
    return QUESTIONS_V3


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
) -> List[Any]:
    """
    Soruları filtrele:
    - category: kategori slug
    - level: beginner / intermediate / advanced
    - search: başlık + açıklamada arama
    - tag: etiket
    """
    questions = load_questions()
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


def get_question(question_id: int, category: Optional[str] = None) -> Optional[Any]:
    """
    ID veya slug'a göre tek Question getirir.
    Önce DB'de slug ile ara, sonra source_id ile, sonra QUESTIONS.py.
    """
    questions = load_questions()

    # 1. Slug ile ara (DB-only, slug unique)
    slug_match = next((q for q in questions if getattr(q, "slug", None) == str(question_id)), None)
    if slug_match:
        if category is None or getattr(slug_match, "category", None) == category:
            return slug_match

    # 2. ID ile ara (legacy + DB source_id)
    for q in questions:
        if q.id != question_id:
            continue
        if category is not None and getattr(q, "category", None) != category:
            continue
        return q
    return None


def get_question_by_slug(slug: str, category: Optional[str] = None) -> Optional[Any]:
    """Slug ile soru getir (DB-first)."""
    questions = load_questions()
    for q in questions:
        if getattr(q, "slug", None) == slug:
            if category is None or getattr(q, "category", None) == category:
                return q
    return None


def get_categories() -> List[Dict]:
    """Kategorileri metadata ile döndür."""
    questions = load_questions()

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
    questions = load_questions()
    return sorted(list({getattr(q, "level", None) for q in questions if getattr(q, "level", None)}))