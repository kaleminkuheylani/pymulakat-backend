# backend/question_loader.py
# Güncellenmiş — kategori opsiyonel kontrol, tag desteği eklendi

from typing import Optional, List, Dict, Any
from data.QUESTIONS import QUESTIONS, Question


def load_questions() -> List[Question]:
    """Supabase'den veya fallback olarak statik QUESTIONS'tan yükler."""
    try:
        from supabase_client import get_supabase
        supabase = get_supabase()
        response = supabase.table("interwiews").select("*").execute()
        if response.data:
            loaded = []
            for q_dict in response.data:
                loaded.append(
                    Question(
                        id=q_dict["id"],
                        title=q_dict["title"],
                        category=q_dict["category"],
                        level=q_dict["level"],
                        description=q_dict["description"],
                        starter_code=q_dict["starter_code"],
                        test_cases=q_dict["test_cases"],
                        hints=q_dict.get("hints", []),
                    )
                )
            return sorted(loaded, key=lambda x: x.id)
    except Exception as e:
        print(f"⚠️ Supabase'den sorular yüklenirken hata: {e}")
    return QUESTIONS


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
    - level: beginner / intermediate / advanced (veya TR: başlangıç / orta / ileri)
    - search: başlık + açıklamada arama
    - tag: etiket (varsa)
    """
    questions = load_questions()
    filtered = questions

    if category:
        filtered = [q for q in filtered if getattr(q, "category", None) == category]

    if level:
        lvl = level.lower().strip()
        # Hem İngilizce hem Türkçe level'ları kabul et
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
    ID'ye göre tek Question getirir. Kategori opsiyonel kontrol.
    - category=None → sadece ID'ye göre ara
    - category=str → ID + kategori eşleşmesi zorunlu
    """
    questions = load_questions()
    for q in questions:
        if q.id != question_id:
            continue
        if category is not None and getattr(q, "category", None) != category:
            continue
        return q
    return None


def get_categories() -> List[Dict]:
    """QUESTIONS'tan unique kategorileri metadata ile döndür."""
    questions = load_questions()
    META = {
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

    unique_slugs = []
    for q in questions:
        cat = getattr(q, "category", None)
        if cat and cat not in unique_slugs:
            unique_slugs.append(cat)

    result = []
    for slug in unique_slugs:
        meta = META.get(slug, {})
        # Soru sayısını hesapla
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