"""routers/tutorials.py'deki 7 fallback tutorial'ı Supabase 'tutorials' tablosuna migrate eder.

IDEMPOTENT — slug çakışırsa günceller.

Kullanım:
    cd /workspace/pymulakat-backend
    python scripts/migrate_tutorials.py

Environment (.env):
    SUPABASE_URL=https://xxxxx.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...
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
    print("[HATA] SUPABASE_URL ve SUPABASE_SERVICE_ROLE_KEY tanimli olmali!")
    sys.exit(1)

from supabase import create_client
from routers.tutorials import FALLBACK_TUTORIALS

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def migrate():
    print("=" * 60)
    print("PythonMulakat — Tutorials Migration")
    print("=" * 60)
    print(f"Hedef: {SUPABASE_URL}")
    print(f"Tutorial sayisi: {len(FALLBACK_TUTORIALS)}")
    print()

    success = 0
    failed = []

    for slug, tutorial in FALLBACK_TUTORIALS.items():
        try:
            row = {
                "slug": tutorial["slug"],
                "title": tutorial["title"],
                "description": tutorial["description"],
                "content_md": tutorial["content_md"],
                "category": tutorial.get("category"),
                "difficulty": tutorial.get("difficulty", "beginner"),
                "reading_time_minutes": tutorial.get("reading_time_minutes", 10),
                "related_question_ids": tutorial.get("related_question_ids", []),
                "faq": tutorial.get("faq", []),
            }

            # UPSERT — slug çakışırsa günceller
            res = supabase.table("tutorials").upsert(row, on_conflict="slug").execute()
            if res.data:
                success += 1
                print(f"  [OK] {slug}: {tutorial['title'][:60]}")
            else:
                failed.append((slug, "bos response"))
        except Exception as e:
            failed.append((slug, str(e)[:100]))
            print(f"  [HATA] {slug}: {e}")

    print()
    print(f"[OK] {success}/{len(FALLBACK_TUTORIALS)} tutorial migrate edildi")

    if failed:
        print(f"\n[!] {len(failed)} tutorial BASARISIZ:")
        for slug, err in failed:
            print(f"    {slug}: {err}")

    # Doğrulama
    try:
        res = supabase.table("tutorials").select("slug, title", count="exact").execute()
        print(f"\n[VERIFY] Toplam tutorial: {res.count}")
    except Exception as e:
        print(f"[VERIFY] Hata: {e}")


if __name__ == "__main__":
    migrate()