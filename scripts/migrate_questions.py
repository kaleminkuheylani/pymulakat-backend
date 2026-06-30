"""QUESTIONS.py + SEO_CONTENT'i Supabase 'interwiews' tablosuna migrate eder.

Tek seferlik script. Çalıştırmak için:
    cd /workspace/pymulakat-backend
    python scripts/migrate_questions.py

Tablo: public.interwiews (mevcut typo — sonradan düzeltilebilir)
Schema: QUESTIONS.py dataclass + SEO_CONTENT.py alanları

UPSERT kullanır — aynı slug varsa günceller, yoksa ekler.
"""

import os
import sys
import asyncio
from pathlib import Path

# Path setup
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Env'den Supabase bilgisi al
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("[HATA] SUPABASE_URL ve SUPABASE_SERVICE_ROLE_KEY env'de olmali")
    sys.exit(1)

from supabase import create_client, Client

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def slugify_title(title: str) -> str:
    """Başlıktan URL-safe slug üret."""
    import re
    s = title.lower()
    # Türkçe karakterleri koru, ama unicode-normalize et
    s = re.sub(r"\s+", "-", s)            # boşluk → tire
    s = re.sub(r"[^a-z0-9\-çğıöşü]", "", s, flags=re.UNICODE)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or f"question-{hash(title)}"


def main():
    # SEO content'i önce uygula (QUESTIONS mutate olur)
    from data.SEO_CONTENT import apply_seo_content
    apply_seo_content()

    from data.QUESTIONS import QUESTIONS

    print(f"\n[INFO] {len(QUESTIONS)} soru bulundu, migrate ediliyor...")

    success = 0
    failed = 0
    relations_to_insert = []

    for q in QUESTIONS:
        try:
            # DB row oluştur
            row = {
                "id": q.id,
                "slug": getattr(q, "slug", None) or slugify_title(q.title),
                "title": q.title,
                "description": q.description or "",
                "category": q.category or "python-basics",
                "level": q.level or "beginner",
                "topic": getattr(q, "topic", None),
                "starter_code": getattr(q, "starter_code", None),
                "function_name": getattr(q, "function_name", None),
                "test_cases": getattr(q, "test_cases", []) or [],
                "hints": getattr(q, "hints", []) or [],
                "tags": getattr(q, "tags", []) or [],
                # SEO alanları
                "explanation": getattr(q, "explanation", None),
                "complexity": getattr(q, "complexity", None),
                "related_concepts": getattr(q, "related_concepts", []) or [],
                "tutorial_slug": getattr(q, "tutorial_slug", None),
                "meta_title": None,
                "meta_description": None,
                "meta_keywords": [],
                "reading_time_minutes": 5,
            }

            # UPSERT — slug çakışırsa güncelle
            res = supabase.table("interwiews").upsert(row, on_conflict="slug").execute()
            if res.data:
                success += 1
                # Relation'ları biriktir
                for rel_id in getattr(q, "related_question_ids", []) or []:
                    relations_to_insert.append({
                        "source_id": q.id,
                        "related_id": rel_id,
                        "relation_type": "related",
                        "weight": 1,
                    })
            else:
                print(f"  [UYARI] #{q.id} {q.title}: bos response")
                failed += 1

        except Exception as e:
            print(f"  [HATA] #{q.id} {q.title}: {e}")
            failed += 1

    print(f"\n[OK] Migration tamamlandi: {success} basarili, {failed} hatali")

    # Relations tablosunu migrate et
    if relations_to_insert:
        print(f"\n[INFO] {len(relations_to_insert)} iliski kaydi ekleniyor...")
        try:
            # Once temizle (idempotent)
            supabase.table("question_relations").delete().gte("source_id", 0).execute()
            # Batch insert (50'şer)
            batch_size = 50
            rel_success = 0
            for i in range(0, len(relations_to_insert), batch_size):
                batch = relations_to_insert[i:i + batch_size]
                res = supabase.table("question_relations").upsert(
                    batch, on_conflict="source_id,related_id"
                ).execute()
                if res.data:
                    rel_success += len(batch)

            print(f"[OK] {rel_success} iliski kaydedildi")
        except Exception as e:
            print(f"[HATA] Relations: {e}")

    print("\n[OK] Migration tamam!")


if __name__ == "__main__":
    main()