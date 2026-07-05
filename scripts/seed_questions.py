#!/usr/bin/env python3
"""QUESTIONS.py'yi oku, Supabase 'questions' tablosuna seed et.

Kullanım:
    export SUPABASE_URL=https://xxx.supabase.co
    export SUPABASE_SERVICE_ROLE_KEY=xxx
    python3 scripts/seed_questions.py

Davranış:
- UPSERT (slug conflict'te update)
- Dry-run için --dry-run flag'i
"""

import argparse
import os
import re
import sys
from pathlib import Path

# Supabase client
try:
    from supabase import create_client, Client
except ImportError:
    print("HATA: supabase-py gerekli. pip install supabase")
    sys.exit(1)

# QUESTIONS.py import (path ekle)
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from data.QUESTIONS import QUESTIONS  # noqa


def slugify(text: str) -> str:
    """Basit slug üretici."""
    s = text.lower()
    # Türkçe karakterleri dönüştür
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    s = s.translate(tr_map)
    # ASCII olmayanları sil
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    # Alfanumerik + tire
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "question"


def parse_question(q_obj, source_id: int) -> dict:
    """Question dataclass'ı DB row formatına çevir."""
    # ID'yi field olarak kullan (Question.id)
    raw_id = getattr(q_obj, "id", source_id)
    title = getattr(q_obj, "title", "")
    description = getattr(q_obj, "description", "") or ""
    explanation = getattr(q_obj, "explanation", None)
    complexity = getattr(q_obj, "complexity", None)
    level = getattr(q_obj, "level", "beginner")
    category = getattr(q_obj, "category", "python-basics")
    starter_code = getattr(q_obj, "starter_code", None)

    # Function name/signature parse
    function_name = None
    function_signature = None
    if starter_code:
        m = re.search(r"def\s+(\w+)\(([^)]*)\)([^:]*):\s*([^\n]*)", starter_code)
        if m:
            function_name = m.group(1)
            params = m.group(2).strip()
            return_type = m.group(4).strip()
            sig = f"def {m.group(1)}({params})"
            if return_type:
                sig += f" -> {return_type}"
            function_signature = sig

    # Slug üret
    slug = slugify(title)

    # Test cases JSONB
    test_cases = getattr(q_obj, "test_cases", []) or []
    test_cases_serializable = []
    for tc in test_cases:
        if isinstance(tc, dict):
            test_cases_serializable.append(tc)
        else:
            test_cases_serializable.append(dict(tc) if hasattr(tc, '__dict__') else tc)

    # Hints
    hints = getattr(q_obj, "hints", []) or []
    hints_serializable = list(hints) if hints else []

    # Related concepts ve tags
    related_concepts = getattr(q_obj, "related_concepts", []) or []
    tags = getattr(q_obj, "tags", []) or []

    return {
        "slug": slug,
        "source_id": raw_id,
        "title": title,
        "description": description,
        "explanation": explanation,
        "complexity": complexity,
        "level": level,
        "category": category,
        "function_name": function_name,
        "function_signature": function_signature,
        "starter_code": starter_code,
        "test_cases": test_cases_serializable,
        "hints": hints_serializable,
        "related_concepts": list(related_concepts),
        "tags": list(tags),
        "is_published": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="DB'ye yazma, sadece göster")
    parser.add_argument("--limit", type=int, default=None, help="Sadece ilk N soruyu seed et")
    args = parser.parse_args()

    print(f"QUESTIONS.py'den {len(QUESTIONS)} soru okundu")

    rows = []
    for i, q in enumerate(QUESTIONS):
        if args.limit and i >= args.limit:
            break
        row = parse_question(q, source_id=i + 1)
        rows.append(row)
        print(f"  [{row['source_id']:>3}] {row['slug']:<40} | {row['level']:<12} | {row['category']}")

    if args.dry_run:
        print(f"\n[DRY RUN] {len(rows)} soru seed edilirdi. Çıkmak için Ctrl+C.")
        return

    # Supabase bağlantısı
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        print("HATA: SUPABASE_URL ve SUPABASE_SERVICE_ROLE_KEY env gerekli.")
        sys.exit(1)

    supabase: Client = create_client(supabase_url, supabase_key)

    # UPSERT (slug üzerinden)
    print(f"\nDB'ye yazılıyor...")
    batch_size = 50
    success = 0
    errors = []
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        try:
            result = supabase.table("questions").upsert(
                batch, on_conflict="slug"
            ).execute()
            success += len(result.data) if result.data else 0
            print(f"  Batch {i // batch_size + 1}: {len(batch)} soru yazildi")
        except Exception as e:
            errors.append({"batch": i, "error": str(e)})
            print(f"  Batch {i // batch_size + 1} HATA: {e}")

    print(f"\nToplam: {success}/{len(rows)} soru basariyla yazildi")
    if errors:
        print(f"Hatalar: {len(errors)}")
        for err in errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()