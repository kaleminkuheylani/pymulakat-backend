"""Mevcut interwiews satırlarının SEO alanlarını QUESTIONS.py'den güncelle.

Sadece UPDATE yapar — INSERT/UPSERT yapmaz.
Title üzerinden eşleşir.

Kullanım:
    cd /workspace/pymulakat-backend
    python scripts/update_seo_fields.py
"""

import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from dotenv import load_dotenv
    load_dotenv(backend_dir / ".env")
except ImportError:
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("[HATA] SUPABASE_URL ve SUPABASE_SERVICE_ROLE_KEY gerekli")
    sys.exit(1)

from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def slugify(title: str) -> str:
    import re
    s = title.lower().strip()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9\-çğıöşü]", "", s, flags=re.UNICODE)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or f"q-{hash(title) % 100000}"


def main():
    # SEO content'i uygula
    from data.SEO_CONTENT import apply_seo_content, SEO_DATA
    from data.QUESTIONS import QUESTIONS
    apply_seo_content()

    print("=" * 60)
    print("SEO Fields Update")
    print("=" * 60)
    print(f"Sorular: {len(QUESTIONS)}")
    print()

    success = 0
    failed = []

    for q in QUESTIONS:
        try:
            update_data = {
                "slug": slugify(q.title),
                "topic": getattr(q, "topic", None),
                "tags": getattr(q, "tags", []) or [],
                "function_name": getattr(q, "function_name", None),
                "starter_code": getattr(q, "starter_code", None),
                "explanation": getattr(q, "explanation", None),
                "complexity": getattr(q, "complexity", None),
                "related_concepts": getattr(q, "related_concepts", []) or [],
                "related_question_ids": getattr(q, "related_question_ids", []) or [],
                "tutorial_slug": getattr(q, "tutorial_slug", None),
                "reading_time_minutes": 5,
            }

            # Title üzerinden UPDATE
            res = supabase.table("interwiews").update(update_data).eq("title", q.title).execute()
            if res.data:
                success += 1
                print(f"  [OK] #{q.id} {q.title[:40]}")
            else:
                # Title eşleşmedi, id ile dene
                res2 = supabase.table("interwiews").update(update_data).eq("id", q.id).execute()
                if res2.data:
                    success += 1
                    print(f"  [OK-by-id] #{q.id} {q.title[:40]}")
                else:
                    failed.append((q.id, q.title, "eslesmedi"))
                    print(f"  [!] #{q.id} {q.title[:40]} — eslesmedi")
        except Exception as e:
            failed.append((q.id, q.title, str(e)[:100]))
            print(f"  [ERR] #{q.id} {q.title[:40]}: {str(e)[:80]}")

    print()
    print(f"[OK] {success}/{len(QUESTIONS)} soru guncellendi")
    if failed:
        print(f"[!] {len(failed)} BASARISIZ:")
        for qid, title, err in failed[:10]:
            print(f"    #{qid} {title}: {err}")

    # Doğrulama
    print("\n[VERIFY] Ilk 3 sorunun SEO alanlari:")
    res = supabase.table("interwiews").select("id, title, slug, complexity, explanation, tutorial_slug").limit(3).execute()
    for row in res.data or []:
        print(f"  #{row['id']} {row['title']}")
        print(f"    slug: {row['slug']}")
        print(f"    complexity: {row['complexity']}")
        print(f"    tutorial_slug: {row['tutorial_slug']}")
        print(f"    explanation: {(row['explanation'] or '')[:80]}...")


if __name__ == "__main__":
    main()