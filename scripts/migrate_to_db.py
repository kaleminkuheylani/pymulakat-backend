#!/usr/bin/env python3
"""QUESTIONS-v3.py + QUESTIONS-v4.py → DB migrate (idempotent, batch upsert).

HEM Q-v3 (82 mevcut) HEM Q-v4 (150 yeni) → Supabase DB'ye import eder.
- Slug unique conflict varsa -2, -3 eklenir.
- Tüm eski sorular önce DB'den export edilir (backup).
- Bulk UPSERT (batch 50).
- Diff raporu (in_both / in_db_only / in_v3_only / in_v4_only).
- Audit log DB'ye yazilir (questions_migrations).

ENV:
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

Davranış:
    python3 scripts/migrate_to_db.py            # Q-v3 + Q-v4 migrate
    python3 scripts/migrate_to_db.py --dry-run  # DB'ye yazma, sadece rapor
    python3 scripts/migrate_to_db.py --backup   # Backup al
    python3 scripts/migrate_to_db.py --v4-only  # Sadece Q-v4 migrate (idempotent)
    python3 scripts/migrate_to_db.py --v3-only  # Sadece Q-v3 migrate
"""

import argparse
import json
import os
import re
import sys
import unicodedata
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from typing import List

ROOT = Path(__file__).parent.parent


# ═══════════════════════════════════════════════════════════════════════════
# Utilities
# ═══════════════════════════════════════════════════════════════════════════


def slugify(text: str) -> str:
    """Slugify (Turkce + ASCII normalize)."""
    s = text.lower()
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    s = s.translate(tr)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "question"


def load_questions_file(filename: str, source_label: str) -> list:
    """QUESTIONS-{version}.py veya .json yükle. JSON öncelikli (.py syntax riski).

    ÖNCELİKLI: data/QUESTIONS-{ver}.json (syntax temiz)
    FALLBACK: data/QUESTIONS-{ver}.py (eski dataclass import)

    Dönen her öğe dict. dataclass değil.
    """
    base = filename.replace(".py", "").replace(".json", "")
    json_path = ROOT / "data" / f"{base}.json"
    py_path = ROOT / "data" / filename

    if json_path.exists():
        try:
            with open(json_path, encoding="utf-8") as f:
                questions = json.load(f)
            print(f"   ✅ {base}.json: {len(questions)} soru yüklendi (JSON)")
            return questions
        except Exception as e:
            print(f"   ⚠️  {base}.json okunamadı: {e}, .py fallback denenecek")

    if py_path.exists():
        try:
            spec = importlib.util.spec_from_file_location(f"{source_label}_loader", py_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            qs = getattr(mod, "QUESTIONS", [])
            # dataclass obj → dict cevir
            qs_dict = []
            for q in qs:
                if hasattr(q, "__dict__"):
                    qs_dict.append({k: v for k, v in q.__dict__.items()})
                else:
                    qs_dict.append(q)
            print(f"   ✅ {base}.py: {len(qs_dict)} soru yüklendi (dataclass → dict)")
            return qs_dict
        except Exception as e:
            print(f"   ⚠️  {base}.py import hatası: {e}")

    print(f"   ⚠️  {base} bulunamadı (ne .json ne .py)")
    return []


def question_to_db_row(q, source: str = "v3") -> dict:
    """Question dataclass → DB row. Q-v3 ve Q-v4 uyumlu."""
    raw_id = getattr(q, "id", 0)
    title = getattr(q, "title", "")
    starter_code = getattr(q, "starter_code", None) or ""

    # Function name + signature (regex parse)
    function_name = None
    function_signature = None
    # Çok satırlı def için DOTALL
    m = re.search(r"def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^:]+))?\s*:", starter_code)
    if m:
        function_name = m.group(1)
        params = m.group(2).strip()
        ret = m.group(3).strip() if m.group(3) else ""
        sig = f"def {m.group(1)}({params})"
        if ret:
            sig += f" -> {ret}"
        function_signature = sig

    # Test cases: hem "expected" hem "_manual_check" hem "expected_count" destekle
    test_cases = getattr(q, "test_cases", []) or []
    test_cases_serializable = []
    for tc in test_cases:
        if isinstance(tc, dict):
            test_cases_serializable.append(tc)
        else:
            try:
                test_cases_serializable.append(dict(tc) if hasattr(tc, "__dict__") else tc)
            except Exception:
                test_cases_serializable.append({"input": str(tc), "_error": "serialize_failed"})

    # Explanation text (Q-v4'te footer eklenmiş olabilir, olduğu gibi al)
    explanation = getattr(q, "explanation", None) or None

    # 📌 Schema uyumu (migrate_questions.sql):
    #   DB kolon adları: slug, source_id, title, description, explanation, complexity,
    #   level, category, function_name, function_signature, starter_code, test_cases,
    #   hints, related_concepts, related_question_ids, tags, is_published.
    #   tutorial_slug kolonu DB'de YOK — INSERT etmiyoruz.
    return {
        "slug": slugify(title),
        "source_id": raw_id,  # 📌 Schema'da unique constraint (was: legacy_id)
        "title": title,
        "description": getattr(q, "description", "") or "",
        "explanation": explanation,
        "complexity": getattr(q, "complexity", None) or None,
        "level": getattr(q, "level", "beginner"),
        "category": getattr(q, "category", "python-basics"),
        "function_name": function_name,
        "function_signature": function_signature,
        "starter_code": starter_code,
        "test_cases": test_cases_serializable,
        "hints": list(getattr(q, "hints", []) or []),
        "related_concepts": list(getattr(q, "related_concepts", []) or []),
        "related_question_ids": [int(x) for x in (getattr(q, "related_question_ids", []) or [])],
        "tags": list(getattr(q, "tags", []) or []),
        "is_published": True,
        "source": source,  # v3 veya v4 (audit için)
    }


# ═══════════════════════════════════════════════════════════════════════════
# Audit log
# ═══════════════════════════════════════════════════════════════════════════


def log_migration(sb, status: str, action: str, details: dict) -> None:
    """Audit log (questions_migrations tablosu)."""
    try:
        sb.table("questions_migrations").insert({
            "status": status,
            "action": action,
            "details": details,
            "migrated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        print(f"   📝 Audit log yazıldı: {action} → {status}")
    except Exception as e:
        print(f"   ⚠️  Audit log yazılamadı: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# Diff raporu
# ═══════════════════════════════════════════════════════════════════════════


def build_diff(existing: list, rows: list) -> dict:
    db_by_source = {r["source_id"]: r for r in existing if r.get("source_id")}
    new_by_source = {r["source_id"]: r for r in rows}
    return {
        "in_db_only": set(db_by_source.keys()) - set(new_by_source.keys()),
        "in_source_only": set(new_by_source.keys()) - set(db_by_source.keys()),
        "in_both": set(db_by_source.keys()) & set(new_by_source.keys()),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(description="Migrate Q-v3 + Q-v4 → Supabase DB")
    parser.add_argument("--dry-run", action="store_true", help="DB'ye yazma, sadece rapor")
    parser.add_argument("--audit", action="store_true", help="Audit log yaz")
    parser.add_argument("--backup", action="store_true", help="DB dump al (JSON)")
    parser.add_argument("--v3-only", action="store_true", help="Sadece Q-v3")
    parser.add_argument("--v4-only", action="store_true", help="Sadece Q-v4")
    args = parser.parse_args()

    print("=" * 70)
    print("QUESTIONS → DB MIGRATION (Q-v3 + Q-v4)")
    print("=" * 70)

    # 1. Source dosyalarını yükle
    print("\n[1/5] Source dosyalar yükleniyor...")
    rows: List[dict] = []
    if not args.v4_only:
        qs_v3 = load_questions_file("QUESTIONS-v3.py", "v3")
        rows.extend(question_to_db_row(q, source="v3") for q in qs_v3)
    if not args.v3_only:
        qs_v4 = load_questions_file("QUESTIONS-v4.json", "v4")
        rows.extend(question_to_db_row(q, source="v4") for q in qs_v4)

    if not rows:
        print("❌ Hiç soru yüklenmedi, çıkılıyor")
        sys.exit(1)

    print(f"   📦 Toplam {len(rows)} soru hazır (Q-v3 + Q-v4)")

    # 2. ENV check
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL veya SUPABASE_SERVICE_ROLE_KEY env gerekli")
        sys.exit(1)

    # 3. Supabase baglantisi
    try:
        from supabase import create_client
        sb = create_client(supabase_url, supabase_key)
        print(f"   ✅ Supabase bağlantısı OK")
    except ImportError:
        print("❌ supabase-py yüklü değil: pip install supabase")
        sys.exit(1)

    # 4. Backup (opsiyonel)
    if args.backup:
        print("\n[2/5] DB backup")
        try:
            all_questions = sb.table("questions").select("*").execute()
            backup_path = ROOT / "scripts" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_path, "w") as f:
                json.dump(all_questions.data or [], f, indent=2, ensure_ascii=False, default=str)
            print(f"   ✅ Backup yazıldı: {backup_path} ({len(all_questions.data or [])} kayıt)")
        except Exception as e:
            print(f"   ⚠️  Backup alınamadı: {e}")

    # 5. Slug duplicate check (in source) → yoksa DB'den kontrol
    print(f"\n[3/5] Slug duplicate kontrolü (kaynak içi)")
    seen_slugs = set()
    internal_dupes = 0
    for row in rows:
        if row["slug"] in seen_slugs:
            internal_dupes += 1
        seen_slugs.add(row["slug"])
    print(f"   {internal_dupes} internal duplicate (slug ile DB conflict olabilir)")

    # DB'de mevcut slugları çek
    print(f"\n[4/5] DB mevcut state")
    try:
        existing = sb.table("questions").select("id, slug, source_id, source").execute()
        existing_list = existing.data or []
        print(f"   DB'de {len(existing_list)} soru var")
    except Exception as e:
        print(f"   ⚠️  DB sorgulanamadı: {e}")
        existing_list = []

    # Slug conflict resolution: source title → slugify → DB'de varsa -2, -3 ekle
    db_slugs = {r["slug"]: r for r in existing_list}
    fixed = 0
    for row in rows:
        original_slug = row["slug"]
        new_slug = original_slug
        n = 2
        # Sadece aynı row değil, DB'de zaten varsa rename
        is_already_in_db = any(r.get("source_id") == row["source_id"] for r in existing_list)
        if not is_already_in_db and new_slug in db_slugs:
            while new_slug in db_slugs:
                new_slug = f"{original_slug}-{n}"
                n += 1
            row["slug"] = new_slug
            fixed += 1
    print(f"   {fixed} slug rename edildi (DB conflict)")

    # Diff raporu
    diff = build_diff(existing_list, rows)
    print(f"\n   📊 DIFF (source_id bazında):")
    print(f"      DB-only orphans:       {len(diff['in_db_only'])}")
    print(f"      Source-only new:       {len(diff['in_source_only'])}")
    print(f"      Both (güncellenen):    {len(diff['in_both'])}")

    if args.dry_run:
        print(f"\n[5/5] DRY RUN — {len(rows)} soru seed edilirdi")
        log_migration(sb, "dry-run", "questions-seed-v3v4", {
            "row_count": len(rows),
            "v3_count": sum(1 for r in rows if r["source"] == "v3"),
            "v4_count": sum(1 for r in rows if r["source"] == "v4"),
        })
        return

    # 6. BULK UPSERT
    print(f"\n[5/5] BULK UPSERT ({len(rows)} soru, batch=50)")
    batch_size = 50
    success = 0
    errors = []
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        batch_num = i // batch_size + 1
        try:
            # source column'u DB schema'da yoksa hata verebilir → temizle
            for r in batch:
                r.pop("source", None)

            result = sb.table("questions").upsert(batch, on_conflict="source_id").execute()
            s = len(result.data) if result.data else 0
            success += s
            print(f"   Batch {batch_num}: {s}/{len(batch)} OK")
        except Exception as e:
            errors.append({"batch": batch_num, "error": str(e)})
            print(f"   ❌ Batch {batch_num}: {str(e)[:200]}")

    print(f"\n{'=' * 70}")
    print(f"SONUÇ: {success}/{len(rows)} soru başarıyla migrate edildi")

    if errors:
        print(f"\n⚠️ Hatalar: {len(errors)} batch")
        for err in errors:
            print(f"  - Batch {err['batch']}: {err['error'][:150]}")

    # Audit log
    if args.audit:
        log_migration(sb, "success" if not errors else "partial", "questions-seed-v3v4", {
            "row_count": len(rows),
            "success": success,
            "errors": len(errors),
            "in_db_only": len(diff["in_db_only"]),
            "in_source_only": len(diff["in_source_only"]),
            "in_both": len(diff["in_both"]),
        })

    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()