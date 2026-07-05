#!/usr/bin/env python3
"""QUESTIONS-v3.py'i oku, Supabase 'questions' tablosuna seed et.

Kullanım (Railway-ready):
    export SUPABASE_URL=https://xxx.supabase.co
    export SUPABASE_SERVICE_ROLE_KEY=xxx
    python3 scripts/seed_questions.py [--dry-run] [--limit N]

Davranış:
- QUESTIONS-v3.py source (82 soru, data-structures dahil)
- UPSERT (legacy_id conflict'te update)
- Bulk insert (batch 50'er)
- Slug duplicate olursa append -N
- --dry-run: DB'ye yazma, sadece listele

onceki migrate scriptlerden farki:
- bulk insert (migrasyon 30s timeout yemez)
- legacy_id ile upsert (slug cakismasi minimize)
"""

import argparse
import os
import re
import sys
import unicodedata
import importlib.util
from pathlib import Path

# Supabase client
try:
    from supabase import create_client
except ImportError:
    print("HATA: supabase-py gerekli")
    sys.exit(1)

# QUESTIONS-v3.py import (dash filename → dynamic load)
ROOT = Path(__file__).parent.parent
v3_path = ROOT / "data" / "QUESTIONS-v3.py"
spec = importlib.util.spec_from_file_location("questions_v3_seed", str(v3_path))
v3_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3_mod)
QUESTIONS = v3_mod.QUESTIONS


def slugify(text: str) -> str:
    """Turkce karakter slugify."""
    s = text.lower()
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    s = s.translate(tr_map)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "question"


def parse_question(q_obj) -> dict:
    """Question dataclass → DB row."""
    raw_id = getattr(q_obj, "id", 0)
    title = getattr(q_obj, "title", "")
    starter_code = getattr(q_obj, "starter_code", None) or ""

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

    test_cases = getattr(q_obj, "test_cases", []) or []
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
        "description": getattr(q_obj, "description", "") or "",
        "explanation": getattr(q_obj, "explanation", None) or None,
        "complexity": getattr(q_obj, "complexity", None) or None,
        "level": getattr(q_obj, "level", "beginner"),
        "category": getattr(q_obj, "category", "python-basics"),
        "function_name": function_name,
        "function_signature": function_signature,
        "starter_code": starter_code,
        "test_cases": test_cases_serializable,
        "hints": list(getattr(q_obj, "hints", []) or []),
        "related_concepts": list(getattr(q_obj, "related_concepts", []) or []),
        "related_question_ids": [int(x) for x in (getattr(q_obj, "related_question_ids", []) or [])],
        "tags": list(getattr(q_obj, "tags", []) or []),
        "is_published": True,
    }


def main():
    parser = argparse.ArgumentParser(description="QUESTIONS-v3.py → Supabase questions seed (legacy_id upsert)")
    parser.add_argument("--dry-run", action="store_true", help="DB'ye yazma")
    parser.add_argument("--limit", type=int, default=None, help="İlk N soru")
    args = parser.parse_args()

    print(f"QUESTIONS-v3.py'den {len(QUESTIONS)} soru okundu")

    rows = [parse_question(q) for q in QUESTIONS]
    if args.limit:
        rows = rows[: args.limit]

    for row in rows:
        print(f"  [{row['legacy_id']:>3}] {row['slug']:<40} | {row['level']:<12} | {row['category']}")

    if args.dry_run:
        print(f"\n[DRY RUN] {len(rows)} soru seed edilirdi.")
        return

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        print("HATA: SUPABASE_URL ve SUPABASE_SERVICE_ROLE_KEY env gerekli.")
        sys.exit(1)

    supabase = create_client(supabase_url, supabase_key)

    # Slug duplicate check — DB'deki slug'larla çakışma
    print("\nDB slug kontrolu (duplicate detection)...")
    existing = supabase.table("questions").select("id, slug, legacy_id").execute()
    existing_slugs = {r["slug"]: r for r in (existing.data or [])}
    used_slugs = set(existing_slugs.keys())

    fixed = 0
    for row in rows:
        if row["slug"] in used_slugs:
            new_slug = row["slug"]
            n = 2
            while new_slug in used_slugs:
                new_slug = f"{row['slug']}-{n}"
                n += 1
            row["slug"] = new_slug
            used_slugs.add(new_slug)
            fixed += 1
        else:
            used_slugs.add(row["slug"])

    print(f"  {fixed} slug rename edildi")

    # BULK UPSERT
    print(f"\nDB'ye yaziliyor: {len(rows)} soru (batch 50)...")
    batch_size = 50
    success = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        try:
            result = supabase.table("questions").upsert(batch, on_conflict="legacy_id").execute()
            s = len(result.data) if result.data else 0
            success += s
            print(f"  Batch {i // batch_size + 1}: {s}/{len(batch)} OK")
        except Exception as e:
            print(f"  Batch {i // batch_size + 1} HATA: {str(e)[:200]}")

    print(f"\nToplam: {success}/{len(rows)} basariyla yazildi")


if __name__ == "__main__":
    main()
