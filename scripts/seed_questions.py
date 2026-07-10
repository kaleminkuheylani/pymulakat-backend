"""
seed_questions.py — Tek seferlik CSV → Supabase DB upsert.

Kullanım:
    python scripts/seed_questions.py

Environment değişkenleri (.env veya Railway Variables'dan):
    SUPABASE_URL                  zorunlu
    SUPABASE_SERVICE_ROLE_KEY     zorunlu (service role, anon key değil)

Davranış:
    - data/QUESTIONS-v3.csv'yi okur.
    - Her satır için CSV'nin 8 alanını + legacy_id'yi Supabase questions
      tablosuna yazar.
    - DB'de aynı legacy_id varsa UPDATE, yoksa INSERT (upsert).
    - Sadece CSV'de tanımlı 8 alan yazılır; slug, meta_*, related_*,
      tags, topic, complexity, explanation, tutorial_slug gibi
      DB-side managed alanlara DOKUNULMAZ.
    - Idempotent: tekrar tekrar çalıştırılabilir.

Çıktı: stdout'ta summary, exit 0/1 (0=success, 1=fatal).
"""
import os
import sys
import csv
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("seed_questions")

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "QUESTIONS-v3.csv"

# DB-side managed alanlar (CSV'de yoksa yazılmaz):
# slug, complexity, explanation, meta_title, meta_description,
# meta_keywords, related_concepts, related_question_ids,
# tags, topic, tutorial_slug

CSV_TO_DB_FIELDS = (
    "description", "starter_code", "test_cases", "hints",
    "function_name", "title", "level", "category",
)


def unquote(value: str) -> str:
    """CSV'de '""foo""bar""' gibi quoted değerleri temizle."""
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return value.replace('""', '"')


def read_csv_rows(csv_path: Path):
    """CSV'den (legacy_id, *CSV_TO_DB_FIELDS) dict listesi döndür."""
    rows = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_id = (row.get("id") or "").strip()
            if not raw_id:
                continue
            try:
                legacy_id = int(raw_id)
            except ValueError:
                log.warning(f"Geçersiz id atlandı: {raw_id!r}")
                continue
            payload = {"legacy_id": legacy_id}
            for fld in CSV_TO_DB_FIELDS:
                payload[fld] = unquote(row.get(fld, ""))
            rows.append(payload)
    return rows


def main() -> int:
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_role_key:
        log.error(
            "Eksik env: SUPABASE_URL ve SUPABASE_SERVICE_ROLE_KEY tanımlı olmalı. "
            "Railway Variables veya local .env'e ekle."
        )
        return 1

    if not CSV_PATH.exists():
        log.error(f"CSV yok: {CSV_PATH}")
        return 1

    log.info(f"CSV okunuyor: {CSV_PATH}")
    rows = read_csv_rows(CSV_PATH)
    log.info(f"Toplam satır: {len(rows)}")

    try:
        from supabase import create_client
    except ImportError:
        log.error(
            "supabase-py yüklü değil. Kurulum: pip install supabase"
        )
        return 1

    sb = create_client(supabase_url, service_role_key)

    succeeded = []
    failed = []
    BATCH = 50
    for i in range(0, len(rows), BATCH):
        batch = rows[i : i + BATCH]
        try:
            result = sb.table("questions").upsert(batch, on_conflict="legacy_id").execute()
            if result.data:
                succeeded.extend([r.get("legacy_id") for r in result.data])
            else:
                failed.extend([
                    {"legacy_id": r["legacy_id"], "reason": "no row upserted"}
                    for r in batch
                ])
        except Exception as e:
            failed.extend([
                {"legacy_id": r["legacy_id"], "reason": str(e)[:200]}
                for r in batch
            ])
        log.info(f"batch [{i}..{i+len(batch)}] done, succeeded+={len(batch)-len(failed)+len(failed)}")

    log.info(
        f"Özet: planned={len(rows)} succeeded={len(succeeded)} "
        f"failed={len(failed)}"
    )
    if failed:
        for f in failed[:20]:
            log.warning(f"  failed: legacy_id={f['legacy_id']} reason={f['reason']}")

    if len(succeeded) == 0:
        log.error("Hiç satır upsert edilmedi — kritik hata.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
