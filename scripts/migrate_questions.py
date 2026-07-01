"""QUESTIONS.py + SEO_CONTENT'i Supabase 'interwiews' tablosuna migrate eder.

IDEMPOTENT — birden fazla çalıştırılabilir.
- Sorular: UPSERT (slug çakışırsa günceller)
- Relations: DELETE+INSERT (source_id'ye göre temizle, yeniden ekle)

Kullanım:
    cd /workspace/pymulakat-backend
    python scripts/migrate_questions.py

Environment (.env):
    SUPABASE_URL=https://xxxxx.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...

Tablo: public.interwiews (mevcut typo — korunuyor)
"""

import os
import sys
import asyncio
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# .env dosyasını yükle (varsa)
try:
    from dotenv import load_dotenv
    load_dotenv(backend_dir / ".env")
except ImportError:
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("[HATA] SUPABASE_URL ve SUPABASE_SERVICE_ROLE_KEY tanımlı olmalı!")
    print()
    print("Çözüm 1: .env dosyası oluştur")
    print('  echo "SUPABASE_URL=..." > .env')
    print('  echo "SUPABASE_SERVICE_ROLE_KEY=..." >> .env')
    print()
    print("Çözüm 2: Environment variable olarak ver")
    print('  SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... python scripts/migrate_questions.py')
    sys.exit(1)

from supabase import create_client, Client

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def slugify_title(title: str) -> str:
    """Başlıktan URL-safe slug üret (Türkçe karakterler ASCII'ye çevrilir)."""
    import re
    # Türkçe karakterleri önce ASCII'ye çevir
    tr_map = {
        'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
        'İ': 'I', 'Ğ': 'G', 'Ü': 'U', 'Ş': 'S', 'Ö': 'O', 'Ç': 'C',
    }
    s = title
    for tr, asc in tr_map.items():
        s = s.replace(tr, asc)
    s = s.lower().strip()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9\-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or f"question-{hash(title) % 100000}"


def tr_to_ascii_slug(text: str) -> str:
    """Türkçe karakterleri ASCII'ye çevirip slug üret."""
    tr_map = {
        'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
        'İ': 'i', 'Ğ': 'g', 'Ü': 'u', 'Ş': 's', 'Ö': 'o', 'Ç': 'c',
    }
    s = text
    for tr, asc in tr_map.items():
        s = s.replace(tr, asc)
    import re
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s


def unique_slug(title: str, qid: int) -> str:
    """Slug + id bazli unique slug. Cozum: qid'yi sona ekle.
    Bu sayede ayni title iki kez olsa bile farkli slug olur."""
    base = slugify_title(title)
    return f"{base}-{qid}"


def test_connection():
    """Bağlantıyı test et — service_role key doğru mu?"""
    try:
        res = supabase.table("interwiews").select("id", count="exact").limit(1).execute()
        count = res.count if hasattr(res, "count") else len(res.data or [])
        print(f"[OK] Baglanti basarili. Mevcut soru sayisi: {count}")
        return True
    except Exception as e:
        print(f"[HATA] Baglanti basarisiz: {e}")
        print("  - SUPABASE_URL dogru mu?")
        print("  - SUPABASE_SERVICE_ROLE_KEY dogru mu? (anon key degil!)")
        print("  - Supabase proje aktif mi?")
        return False


def migrate_questions():
    """Ana migration akışı — UPDATE by slug (idempotent), INSERT if missing."""
    # SEO content'i önce uygula (QUESTIONS mutate olur)
    print("\n[1/3] SEO content uygulaniyor...")
    from data.SEO_CONTENT import apply_seo_content
    apply_seo_content()

    from data.QUESTIONS import QUESTIONS

    print(f"\n[2/3] {len(QUESTIONS)} soru migrate ediliyor (UPDATE-by-slug)...")

    # Once mevcut title -> id map'i al
    try:
        existing = supabase.table("interwiews").select("id, title, slug").execute()
        title_to_id = {row["title"]: row["id"] for row in (existing.data or [])}
        slug_to_id = {row["slug"]: row["id"] for row in (existing.data or []) if row.get("slug")}
        print(f"  [INFO] Mevcut soru sayisi: {len(title_to_id)}")
    except Exception as e:
        print(f"  [WARN] Mevcut veriler alinamadi: {e}")
        title_to_id = {}
        slug_to_id = {}

    success = 0
    failed = []
    relations_to_insert = []
    skipped = 0

    for q in QUESTIONS:
        try:
            row = {
                "id": q.id,
                "slug": getattr(q, "slug", None) or unique_slug(q.title, q.id),
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

            # Mevcut satir var mi? (title veya slug ile)
            existing_id = title_to_id.get(q.title) or slug_to_id.get(row["slug"])

            if existing_id:
                # UPDATE — sadece SEO alanlarini guncelle
                update_res = supabase.table("interwiews").update({
                    "slug": row["slug"],
                    "explanation": row["explanation"],
                    "complexity": row["complexity"],
                    "related_concepts": row["related_concepts"],
                    "related_question_ids": getattr(q, "related_question_ids", []) or [],
                    "tutorial_slug": row["tutorial_slug"],
                    "hints": row["hints"],
                    "function_name": row["function_name"],
                    "starter_code": row["starter_code"],
                    "topic": row["topic"],
                    "tags": row["tags"],
                    "reading_time_minutes": row["reading_time_minutes"],
                }).eq("id", existing_id).execute()
                success += 1  # UPDATE her zaman basarili sayilir (bos data olabilir)
                skipped += 1
            else:
                # INSERT — yeni satir
                # id çakışmasını önle: id'siz insert yap, DB otomatik atasin
                insert_row = {k: v for k, v in row.items() if k != "id"}
                insert_res = supabase.table("interwiews").insert(insert_row).execute()
                if insert_res.data:
                    success += 1
                    new_id = insert_res.data[0].get("id")
                    title_to_id[q.title] = new_id
                    slug_to_id[row["slug"]] = new_id
                else:
                    failed.append((q.id, q.title, "insert bos response"))

            # Relation'ları biriktir
            for rel_id in getattr(q, "related_question_ids", []) or []:
                relations_to_insert.append({
                    "source_id": q.id,
                    "related_id": rel_id,
                    "relation_type": "related",
                    "weight": 1,
                })

        except Exception as e:
            failed.append((q.id, q.title, str(e)[:150]))

    print(f"\n  [OK] {success}/{len(QUESTIONS)} soru basariyla migrate edildi")
    if failed:
        print(f"  [!] {len(failed)} soru BASARISIZ:")
        for qid, title, err in failed[:10]:
            print(f"      #{qid} {title}: {err}")
        if len(failed) > 10:
            print(f"      ... ve {len(failed) - 10} tane daha")

    return relations_to_insert


def migrate_relations(relations: list):
    """Relation'ları ekle (DELETE+INSERT — idempotent)."""
    print(f"\n[3/3] {len(relations)} iliski kaydi ekleniyor...")

    if not relations:
        print("  [SKIP] Hic iliski yok")
        return

    try:
        # Once temizle (idempotent — tekrar tekrar çalıştırılabilir)
        supabase.table("question_relations").delete().gte("source_id", 0).execute()

        # Batch insert (50'şer — Supabase API limiti)
        batch_size = 50
        rel_success = 0
        for i in range(0, len(relations), batch_size):
            batch = relations[i:i + batch_size]
            res = supabase.table("question_relations").upsert(
                batch, on_conflict="source_id,related_id"
            ).execute()
            if res.data:
                rel_success += len(batch)

        print(f"  [OK] {rel_success}/{len(relations)} iliski kaydedildi")
    except Exception as e:
        print(f"  [HATA] Relations: {e}")


def verify_migration():
    """Migration sonrası doğrulama."""
    print("\n[VERIFY] Migration dogrulaniyor...")

    try:
        # Toplam soru
        res = supabase.table("interwiews").select("id, slug, category, level, has_seo:explanation", count="exact").execute()
        total = res.count if hasattr(res, "count") else len(res.data or [])

        # SEO content'i olan sorular
        seo_count = sum(1 for q in (res.data or []) if q.get("has_seo"))

        # Relation sayısı
        rel_res = supabase.table("question_relations").select("id", count="exact").limit(1).execute()
        rel_count = rel_res.count if hasattr(rel_res, "count") else 0

        print(f"  Toplam soru: {total}")
        print(f"  SEO content olan: {seo_count}/{total}")
        print(f"  Iliski sayisi: {rel_count}")

        # Kategori dağılımı
        cats = {}
        for q in (res.data or []):
            cat = q.get("category", "?")
            cats[cat] = cats.get(cat, 0) + 1

        print(f"\n  Kategoriler:")
        for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"    {cat}: {cnt}")

        print("\n[OK] Migration basariyla tamamlandi!")
        return True
    except Exception as e:
        print(f"  [HATA] Dogrulama basarisiz: {e}")
        return False


def main():
    print("=" * 60)
    print("PythonMulakat — DB Migration")
    print("=" * 60)
    print(f"Hedef: {SUPABASE_URL}")
    print()

    if not test_connection():
        sys.exit(1)

    relations = migrate_questions()
    migrate_relations(relations)
    verify_migration()


if __name__ == "__main__":
    main()