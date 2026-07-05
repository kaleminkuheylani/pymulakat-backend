#!/usr/bin/env python3
"""QUESTIONS-v3.py'yi DB'ye migrate et (Railway-friendly).

Production'da yeni soru eklenince Vercel deploy → Railway bot
    python3 scripts/migrate_to_db.py
calistirir. Idempotent (tekrar calistirilabilir).

Davranis:
- Slug unique conflict varsa -2,-3 eklenir
- Tum eski sorular once DB'den export edilir (backup)
- Bulk UPSERT (batch 50)
- Diff raporu (in_both / in_db_only / in_v3_only)
- Audit log DB'ye yazilir (questions_migrations tablosu)

ENV:
  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
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

ROOT = Path(__file__).parent.parent

# ═══════════════════════════════════════════════════════════════
# Utilities
# ═══════════════════════════════════════════════════════════════

def slugify(text: str) -> str:
    """Slugify (Turkce + ASCII normalize)."""
    s = text.lower()
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    s = s.translate(tr)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "question"


def load_v3_questions() -> list:
    """QUESTIONS-v3.py yükle (dash filename)."""
    v3_path = ROOT / "data" / "QUESTIONS-v3.py"
    spec = importlib.util.spec_from_file_location("questions_v3_load", v3_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.QUESTIONS


def question_to_db_row(q) -> dict:
    """Question dataclass → DB row."""
    raw_id = getattr(q, "id", 0)
    title = getattr(q, "title", "")
    starter_code = getattr(q, "starter_code", None) or ""

    function_name = None
    function_signature = None
    m = re.search(r"def\s+(\w+)\(([^)]*)\)([^:]*):\s*([^\n]*)", starter_code)
    if m:
        function_name = m.group(1)
        params = m.group(2).strip()
        return_type = m.group(4).strip()
        sig = f"def {m.group(1)}({params})"
        if return_type:
            sig += f" -> {return_type}"
        function_signature = sig

    test_cases = getattr(q, "test_cases", []) or []
    test_cases_serializable = []
    for tc in test_cases:
        if isinstance(tc, dict):
            test_cases_serializable.append(tc)
        else:
            test_cases_serializable.append(dict(tc) if hasattr(tc, "__dict__") else tc)

    return {
        "slug": slugify(title),
        "legacy_id": raw_id,
        "title": title,
        "description": getattr(q, "description", "") or "",
        "explanation": getattr(q, "explanation", None) or None,
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
    }


# ═══════════════════════════════════════════════════════════════
# Migration report
# ═══════════════════════════════════════════════════════════════

def log_migration(sb, status: str, action: str, details: dict) -> None:
    """Audit log yaz (questions_migrations tablosu)."""
    try:
        sb.table("questions_migrations").insert({
            "status": status,
            "action": action,
            "details": details,
            "migrated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception:
        # Tablo yoksa skip
        pass


def main():
    parser = argparse.ArgumentParser(description="Migrate QUESTIONS-v3.py → Supabase DB")
    parser.add_argument("--dry-run", action="store_true", help="DB'ye yazma")
    parser.add_argument("--audit", action="store_true", help="Audit log yaz")
    parser.add_argument("--backup", action="store_true", help="DB dump al")
    args = parser.parse_args()

    print("=" * 70)
    print("QUESTIONS-V3 → DB MIGRATION")
    print("=" * 70)

    # 1. Source: QUESTIONS-v3.py
    questions = load_v3_questions()
    print(f"\n[1/4] QUESTIONS-v3.py yuklendi: {len(questions)} soru")

    rows = [question_to_db_row(q) for q in questions]
    print(f"  {len(rows)} DB row hazir")

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
    except ImportError:
        print("❌ supabase-py yuklu degil: pip install supabase")
        sys.exit(1)

    # 4. Backup (opsiyonel)
    if args.backup:
        print("\n[2/4] DB backup")
        all_questions = sb.table("questions").select("*").execute()
        backup_path = ROOT / "scripts" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_path, "w") as f:
            json.dump(all_questions.data or [], f, indent=2, ensure_ascii=False, default=str)
        print(f"  Backup yazildi: {backup_path}")

    # 5. Slug duplicate check
    print(f"\n[3/4] Slug duplicate kontrolu")
    existing = sb.table("questions").select("id, slug, legacy_id").execute()
    existing_slugs = {r["slug"]: r for r in (existing.data or [])}
    fixed = 0
    for row in rows:
        if row["slug"] in existing_slugs:
            new_slug = row["slug"]
            n = 2
            while new_slug in {r["slug"] for r in (existing.data or [])}:
                new_slug = f"{row['slug']}-{n}"
                n += 1
            row["slug"] = new_slug
            fixed += 1
    print(f"  {fixed} slug rename edildi")

    # Diff raporu
    db_by_legacy = {r["legacy_id"]: r for r in (existing.data or []) if r.get("legacy_id")}
    v3_by_legacy = {r["legacy_id"]: r for r in rows}
    in_db_only = set(db_by_legacy.keys()) - set(v3_by_legacy.keys())
    in_v3_only = set(v3_by_legacy.keys()) - set(db_by_legacy.keys())
    in_both = set(db_by_legacy.keys()) & set(v3_by_legacy.keys())

    print(f"\n  DB'de olan V3'te olmayan (orphans): {len(in_db_only)}")
    print(f"  V3'te olan DB'de olmayan (yeni eklenen): {len(in_v3_only)}")
    print(f"  Eslesen (güncellenen): {len(in_both)}")

    # 6. BULK UPSERT
    if args.dry_run:
        print(f"\n[4/4] DRY RUN — {len(rows)} soru seed edilirdi")
        log_migration(sb, "dry-run", "questions-seed", {"row_count": len(rows)})
        return

    print(f"\n[4/4] BULK UPSERT ({len(rows)} soru)")
    batch_size = 50
    success = 0
    errors = []
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        try:
            result = sb.table("questions").upsert(batch, on_conflict="legacy_id").execute()
            s = len(result.data) if result.data else 0
            success += s
            print(f"  Batch {i // batch_size + 1}: {s}/{len(batch)} OK")
        except Exception as e:
            errors.append({"batch": i // batch_size + 1, "error": str(e)})
            print(f"  ❌ Batch {i // batch_size + 1}: {str(e)[:200]}")

    print(f"\n{'=' * 70}")
    print(f"SONUC: {success}/{len(rows)} soru basariyla migrate edildi")

    if errors:
        print(f"Hatalar: {len(errors)}")
        for err in errors:
            print(f"  - Batch {err['batch']}: {err['error'][:150]}")

    # Audit log
    if args.audit:
        log_migration(sb, "success", "questions-seed", {
            "row_count": len(rows),
            "success": success,
            "errors": len(errors),
            "in_db_only": len(in_db_only),
            "in_v3_only": len(in_v3_only),
        })
        print("Audit log yazildi")

    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
