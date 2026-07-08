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
        fallback = _load_questions_fallback()
        if fallback:
            print(f"🔄 Fallback: data/QUESTIONS-v3.py'den {len(fallback)} soru yüklendi (db_error={bool(db_error)}, db_empty={not db_questions})")
            _CACHE["data"] = fallback
            _CACHE["ts"] = now
            return fallback

    # Hem DB hem fallback boş
    if _CACHE["data"] is not None:
        return _CACHE["data"]
    return []


def _load_questions_fallback() -> List[Question]:
    """DB boş/başarısız olduğunda soruları yerleşik kaynaklardan yükle.

    Öncelik sırası:
      1. data/QUESTIONS-v3.json       (build artifact — runtime primary)
      2. data/QUESTIONS_FACTORY.csv   (kaynak dosyası — runtime parse)
      3. data/QUESTIONS-v3.py         (LEGACY: eski dataclass, syntax bozuk olabilir)

    Her adım sessizce başarısız olursa bir sonrakine düşer.
    CSV → JSON pipeline: scripts/csv_to_json.py kullanılır.
    V4 dosyalari (.json.disabled / .py.disabled) devre dişi.
    """
    import importlib.util
    from pathlib import Path

    data_dir = Path(__file__).resolve().parent / "data"

    def _slugify(t: str) -> str:
        import re as _re, unicodedata as _u
        s = t.lower()
        tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
        s = s.translate(tr)
        s = _u.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
        s = _re.sub(r"[^a-z0-9]+", "-", s).strip("-")
        return s[:80] or "question"

    # ── 1. V3.json — ÖNCELİKLİ ─────────────────────────────────
    v4_json = data_dir / "QUESTIONS-v3.json"
    if v4_json.exists():
        try:
            import json as _json
            with open(v4_json, encoding="utf-8") as _f:
                raw = _json.load(_f)
            if not isinstance(raw, list) or not raw:
                raise ValueError("V3.json boş veya yanlış format")

            used: set = set()
            def _ensure_slug(title: str, qid: int) -> str:
                base = _slugify(title or f"question-{qid}")
                cand = base
                n = 2
                while cand in used:
                    cand = f"{base}-{n}"
                    n += 1
                used.add(cand)
                return cand

            result: List[Question] = []
            for q in raw:
                slug_val = q.get("slug") or _ensure_slug(q.get("title", ""), q.get("id", 0))
                result.append(Question(
                    id=q["id"],
                    title=q.get("title", ""),
                    category=q.get("category", "python-basics"),
                    level=q.get("level", "beginner"),
                    description=q.get("description", ""),
                    starter_code=q.get("starter_code"),
                    test_cases=q.get("test_cases", []) or [],
                    hints=q.get("hints", []) or [],
                    slug=slug_val,
                    related_question_ids=list(q.get("related_question_ids", []) or []),
                    explanation=q.get("explanation"),
                    complexity=q.get("complexity"),
                    tags=list(q.get("tags", []) or []),
                    function_name=None,
                    topic=None,
                    tutorial_slug=q.get("tutorial_slug"),
                    related_concepts=list(q.get("related_concepts", []) or []),
                    meta_title=None,
                    meta_description=None,
                    meta_keywords=[],
                ))
            print(f"✅ Fallback: V3.json'dan {len(result)} soru yüklendi")
            return result
        except Exception as e:
            print(f"⚠️ Fallback V3.json okunamadı: {e}")

    # ── 2. FACTORY.csv — Runtime parse (kaynak dosyası) ────────────────
    factory_csv = data_dir / "QUESTIONS_FACTORY.csv"
    if factory_csv.exists():
        try:
            import csv as _csv
            with open(factory_csv, encoding="utf-8", newline="") as _f:
                reader = _csv.DictReader(_f)
                raw_csv = list(reader)
            if not raw_csv:
                raise ValueError("FACTORY.csv boş")

            used_csv: set = set()
            def _ensure_slug_csv(title: str, qid: int) -> str:
                base = _slugify(title or f"question-{qid}")
                cand = base
                n = 2
                while cand in used_csv:
                    cand = f"{base}-{n}"
                    n += 1
                used_csv.add(cand)
                return cand

            result_csv: List[Question] = []
            for q in raw_csv:
                # test_cases / hints CSV'de JSON string olarak duruyor
                try:
                    tc = _json.loads(q.get("test_cases", "") or "[]")
                except Exception:
                    tc = []
                try:
                    ht = _json.loads(q.get("hints", "") or "[]")
                except Exception:
                    ht = []
                slug_val = q.get("slug") or _ensure_slug_csv(q.get("title", ""), int(q.get("id", 0) or 0))
                result_csv.append(Question(
                    id=int(q["id"]),
                    title=q.get("title", ""),
                    category=q.get("category", "python-basics"),
                    level=q.get("level", "beginner"),
                    description=q.get("description", ""),
                    starter_code=q.get("starter_code"),
                    test_cases=tc,
                    hints=ht,
                    slug=slug_val,
                    related_question_ids=[],
                    explanation=None,
                    complexity=None,
                    tags=[],
                    function_name=None,
                    topic=None,
                    tutorial_slug=None,
                    related_concepts=[],
                    meta_title=None,
                    meta_description=None,
                    meta_keywords=[],
                ))
            print(f"✅ Fallback: FACTORY.csv'den {len(result_csv)} soru yüklendi")
            return result_csv
        except Exception as e:
            print(f"⚠️ Fallback FACTORY.csv okunamadı: {e}")

    # ── 3. V2.py — LEGACY (syntax hatalı olabilir) ───────────────
    v3_py = data_dir / "QUESTIONS-v3.py"
    if not v3_py.exists():
        return []

    try:
        spec = importlib.util.spec_from_file_location("questions_v3_fallback", v3_py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:
        print(f"⚠️ Fallback V3.py import hatası (legacy): {e}")
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

    # Slug üret (data'da slug alanları None olabilir)
    used_slugs: set = set()
    def _slugify(t: str) -> str:
        import re as _re, unicodedata as _u
        s = t.lower()
        tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
        s = s.translate(tr)
        s = _u.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
        s = _re.sub(r"[^a-z0-9]+", "-", s).strip("-")
        return s[:80] or "question"

    def _ensure_slug(title: str) -> str:
        base = _slugify(title or "question")
        candidate = base
        n = 2
        while candidate in used_slugs:
            candidate = f"{base}-{n}"
            n += 1
        used_slugs.add(candidate)
        return candidate

    # Question dataclass → DB row dict → Question dataclass (loader)
    result: List[Question] = []
    for q in questions_raw:
        # Slug None ise title'dan üret (slug benzersizliği DB UNIQUE ile uyumlu)
        slug_val = getattr(q, "slug", None)
        if not slug_val:
            slug_val = _ensure_slug(q.title or f"question-{q.id}")

        result.append(Question(
            id=q.id,
            title=q.title,
            category=q.category,
            level=q.level,
            description=getattr(q, "description", "") or "",
            starter_code=getattr(q, "starter_code", None),
            test_cases=getattr(q, "test_cases", []) or [],
            hints=getattr(q, "hints", []) or [],
            slug=slug_val,
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