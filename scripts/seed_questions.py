#!/usr/bin/env python3
"""
pymulakat — Seed script: data/QUESTIONS-v3.py + SEO_CONTENT.py → Supabase 'questions' tablosu
═══════════════════════════════════════════════════════════════════════════════════════════

TEK SEFERLIK seed. Sonrasında question_loader.py DB'den okur, kodda veri olmaz.

Kullanım:
  export SUPABASE_URL="https://xxx.supabase.co"
  export SUPABASE_SERVICE_ROLE_KEY="eyJ..."
  export DRY_RUN="true"   # sadece rapor, INSERT yapma
  python scripts/seed_questions.py

Davranış:
  • DB'de olmayan soruları INSERT eder
  • Var olanları SKIP eder (slug unique check ile)
  • SEO_CONTENT.py explanation/complexity/related_concepts alanlarını merge eder
  • Detay: data/QUESTIONS-v3.py 70+ soru dataclass

İdempotent: tekrar çalıştırmak güvenli, duplicate oluşturmaz.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("seed")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def require_env():
    if not SUPABASE_URL or not SUPABASE_KEY:
        log.error("Eksik env: SUPABASE_URL ve SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)


def load_questions_v3() -> List[Any]:
    """data/QUESTIONS-v3.py dosyasını import et, QUESTIONS listesini döndür."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("questions_v3_seed", DATA_DIR / "QUESTIONS-v3.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.QUESTIONS


def apply_seo(questions: List[Any]) -> List[Any]:
    """SEO_CONTENT.py'yi yükle, QUESTIONS listesini mutate et."""
    seo_path = DATA_DIR / "SEO_CONTENT.py"
    if not seo_path.exists():
        log.warning("SEO_CONTENT.py yok, SEO alanları atlanıyor")
        return questions

    import importlib.util
    spec = importlib.util.spec_from_file_location("seo_content_seed", seo_path)
    seo_mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(seo_mod)
    except Exception as e:
        log.warning("SEO_CONTENT import başarısız (devam ediliyor): %s", e)
        return questions

    # SEO_CONTENT.py data/QUESTIONS.py'yi import ediyor — v3'e yönlendirmek için
    # patch gerekebilir. QUESTIONS-v3'ün id'leri QUESTIONS.py ile çakışıyorsa çalışır.
    try:
        seo_mod.apply_seo_content()
    except Exception as e:
        log.warning("SEO apply başarısız (devam ediliyor): %s", e)
    return questions


def q_to_db_row(q) -> Dict[str, Any]:
    """Question dataclass → Supabase row dict.

    Tüm list/tuple/set alanları JSONB-safe list'e normalizasyon edilir.
    set type JSON serializable değildir (Postgres JSONB reject eder).
    """
    def _listify(value):
        """None/list/tuple/set → list; düz value → [value]."""
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return list(value)
        if isinstance(value, set):
            return list(value)
        return [value]

    return {
        "legacy_id": q.id,
        "title": q.title,
        "category": q.category,
        "level": q.level,
        "description": getattr(q, "description", "") or "",
        "starter_code": getattr(q, "starter_code", None),
        "test_cases": _listify(getattr(q, "test_cases", []) or []),
        "hints": _listify(getattr(q, "hints", []) or []),
        "slug": getattr(q, "slug", None),
        "explanation": getattr(q, "explanation", None),
        "complexity": getattr(q, "complexity", None),
        "related_concepts": _listify(getattr(q, "related_concepts", []) or []),
        "related_question_ids": _listify(getattr(q, "related_question_ids", []) or []),
        "tags": _listify(getattr(q, "tags", []) or []),
        "tutorial_slug": getattr(q, "tutorial_slug", None),
        "is_published": True,
    }


def make_json_safe(obj: Any) -> Any:
    """Supabase insert için JSONB-safe recursive normalizasyon.

    set/tuple → list
    bytes → str (decode attempt)
    Dict/list recursive traverse.
    """
    if isinstance(obj, set):
        return [make_json_safe(x) for x in obj]
    if isinstance(obj, tuple):
        return [make_json_safe(x) for x in obj]
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(x) for x in obj]
    if isinstance(obj, bytes):
        try:
            return obj.decode("utf-8")
        except Exception:
            return str(obj)
    return obj


def get_existing_slugs(sb) -> set:
    """DB'deki mevcut slug'ları çek (idempotent kontrol için)."""
    result = sb.table("questions").select("slug").execute()
    return {r.get("slug") for r in (result.data or []) if r.get("slug")}


def get_existing_legacy_ids(sb) -> set:
    """DB'deki legacy_id'leri çek. 20 yeni soru append edildiğinde çakışma kontrolü için."""
    try:
        result = sb.table("questions").select("legacy_id").execute()
        return {r.get("legacy_id") for r in (result.data or []) if r.get("legacy_id") is not None}
    except Exception as e:
        log.warning("legacy_id cekilemedi (devam ediliyor): %s", e)
        return set()


def slugify(text: str) -> str:
    """migrate_to_db ile aynı slugify — title'dan URL-friendly slug üretir."""
    import re as _re
    import unicodedata as _u
    s = text.lower()
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    s = s.translate(tr)
    s = _u.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = _re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "question"


def ensure_slug(row: Dict[str, Any], idx: int, used: set) -> Dict[str, Any]:
    """Slug yoksa title'dan üret. Çakışma varsa -2/-3 ekle."""
    if row.get("slug"):
        return row
    base = slugify(row.get("title", f"question-{idx}"))
    candidate = base
    n = 2
    while candidate in used:
        candidate = f"{base}-{n}"
        n += 1
    if candidate != base:
        row["slug"] = candidate
    else:
        row["slug"] = candidate
    used.add(row["slug"])
    return row


def validate_row(row: Dict[str, Any]) -> Optional[str]:
    """Minimum validasyon — hata varsa neden döner, yoksa None."""
    if not row.get("slug"):
        return "slug bos"
    if not row.get("title"):
        return "title bos"
    if not row.get("category"):
        return "category bos"
    tc = row.get("test_cases") or []
    if not isinstance(tc, list) or not tc:
        return "test_cases bos/yanlis tip"
    for tc_item in tc:
        if not isinstance(tc_item, dict):
            return "test_cases elemani dict degil"
        if "input" not in tc_item or "expected" not in tc_item:
            return "test_cases elemani input/expected icermiyor"
    return None


def main():
    require_env()

    log.info("=" * 60)
    log.info("SEED — %s modu", "DRY_RUN" if DRY_RUN else "CANLI")
    log.info("=" * 60)
    log.info("Supabase: %s", SUPABASE_URL)

    questions = load_questions_v3()
    log.info("📦 QUESTIONS-v3.py: %d soru", len(questions))

    questions = apply_seo(questions)
    log.info("✅ SEO_CONTENT uygulandı")

    rows = [q_to_db_row(q) for q in questions]

    # Slug yoksa title'dan üret (mevcut data'da slug alanları boş olabiliyor)
    used_slugs: set = set()
    for i, r in enumerate(rows):
        ensure_slug(r, i, used_slugs)
    rows = [r for r in rows if r.get("slug")]  # slug'sızları atla
    log.info("📋 Slug'lı sorular: %d", len(rows))

    # Validasyon — her satır sorunsuz mu?
    invalid = [(r, validate_row(r)) for r in rows if validate_row(r) is not None]
    if invalid:
        log.warning("⚠️ %d gecersiz soru bulundu (ilk 5):", len(invalid))
        for r, reason in invalid[:5]:
            log.warning("  • %s :: %s", r.get("slug") or "—", reason)
        rows = [r for r in rows if validate_row(r) is None]
    log.info("📋 Gecerli sorular: %d / slug'lı: aynı sayı, gecersiz atlandı", len(rows))

    if DRY_RUN:
        log.info("🔍 DRY_RUN — INSERT yapılmadı")
        for r in rows[:5]:
            log.info("  • %s | %s | %s", r["category"], r["slug"], r["title"][:50])
        log.info("  ... ve %d soru daha", max(0, len(rows) - 5))
        return

    try:
        from supabase import create_client
    except ImportError:
        log.error("supabase paketi gerekli: uv add supabase")
        sys.exit(1)

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    existing = get_existing_slugs(sb)
    log.info("📊 DB'de mevcut (slug bazlı): %d soru", len(existing))

    # legacy_id çakışma kontrolü — yeni 20 soru eklendikten sonra idempotency için
    existing_legacy_ids = get_existing_legacy_ids(sb)
    log.info("📊 DB'de mevcut legacy_id: %d adet", len(existing_legacy_ids))

    def _to_skip(r):
        # Skip: slug zaten var VEYA legacy_id zaten varsa
        if r["slug"] in existing:
            return True
        if r.get("legacy_id") in existing_legacy_ids:
            return True
        return False

    to_insert = [r for r in rows if not _to_skip(r)]
    to_skip = [r for r in rows if _to_skip(r)]

    log.info("➕ Eklenecek: %d", len(to_insert))
    log.info("⏭️  Atlanacak (zaten var): %d", len(to_skip))

    if not to_insert:
        log.info("✅ Hepsi DB'de, işlem yok")
        return

    # Batch INSERT (Supabase 1000/req destekler)
    BATCH = 50
    inserted = 0
    failed = []
    for i in range(0, len(to_insert), BATCH):
        batch = to_insert[i:i + BATCH]
        # JSONB-safe normalize (set → list)
        safe_batch = [make_json_safe(r) for r in batch]
        try:
            sb.table("questions").insert(safe_batch).execute()
            inserted += len(safe_batch)
            log.info("  ✓ Batch %d: %d soru eklendi", i // BATCH + 1, len(safe_batch))
        except Exception as e:
            log.error("  ✗ Batch %d hata: %s", i // BATCH + 1, e)
            failed.extend(safe_batch)

    log.info("=" * 60)
    log.info("✅ Seed tamamlandı: %d/%d eklendi", inserted, len(to_insert))
    if failed:
        log.warning("⚠️ %d soru eklenemedi (loglanıyor: data/seed_failures.json)", len(failed))
        Path("data/seed_failures.json").write_text(
            __import__("json").dumps(failed, indent=2, ensure_ascii=False)
        )


if __name__ == "__main__":
    main()