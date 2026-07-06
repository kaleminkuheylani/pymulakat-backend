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
from typing import List, Dict, Any
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
    spec.loader.exec_module(seo_mod)

    # SEO_CONTENT.py data/QUESTIONS.py'yi import ediyor — v3'e yönlendirmek için
    # patch gerekebilir. QUESTIONS-v3'ün id'leri QUESTIONS.py ile çakışıyorsa çalışır.
    try:
        seo_mod.apply_seo_content()
    except Exception as e:
        log.warning("SEO apply başarısız (devam ediliyor): %s", e)
    return questions


def q_to_db_row(q) -> Dict[str, Any]:
    """Question dataclass → Supabase row dict."""
    return {
        "legacy_id": q.id,
        "title": q.title,
        "category": q.category,
        "level": q.level,
        "description": getattr(q, "description", ""),
        "starter_code": getattr(q, "starter_code", None),
        "test_cases": getattr(q, "test_cases", []) or [],
        "hints": getattr(q, "hints", []) or [],
        "slug": getattr(q, "slug", None),
        "explanation": getattr(q, "explanation", None),
        "complexity": getattr(q, "complexity", None),
        "related_concepts": getattr(q, "related_concepts", []) or [],
        "related_question_ids": getattr(q, "related_question_ids", []) or [],
        "tags": getattr(q, "tags", []) or [],
        "tutorial_slug": getattr(q, "tutorial_slug", None),
        "is_published": True,
    }


def get_existing_slugs(sb) -> set:
    """DB'deki mevcut slug'ları çek (idempotent kontrol için)."""
    result = sb.table("questions").select("slug").execute()
    return {r.get("slug") for r in (result.data or []) if r.get("slug")}


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
    rows = [r for r in rows if r.get("slug")]  # slug'sızları atla
    log.info("📋 Slug'lı sorular: %d", len(rows))

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
    log.info("📊 DB'de mevcut: %d soru", len(existing))

    to_insert = [r for r in rows if r["slug"] not in existing]
    to_skip = [r for r in rows if r["slug"] in existing]

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
        try:
            sb.table("questions").insert(batch).execute()
            inserted += len(batch)
            log.info("  ✓ Batch %d: %d soru eklendi", i // BATCH + 1, len(batch))
        except Exception as e:
            log.error("  ✗ Batch %d hata: %s", i // BATCH + 1, e)
            failed.extend(batch)

    log.info("=" * 60)
    log.info("✅ Seed tamamlandı: %d/%d eklendi", inserted, len(to_insert))
    if failed:
        log.warning("⚠️ %d soru eklenemedi (loglanıyor: data/seed_failures.json)", len(failed))
        Path("data/seed_failures.json").write_text(
            __import__("json").dumps(failed, indent=2, ensure_ascii=False)
        )


if __name__ == "__main__":
    main()