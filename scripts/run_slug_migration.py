#!/usr/bin/env python3
"""
Slug Migration Script — interviews tablosuna slug kolonu ekler + tüm sorular için slug üretir.

Lokal veya Railway shell'de çalıştırılabilir:
    python3 scripts/run_slug_migration.py

ENV:
    DATABASE_URL: Supabase Postgres connection string
    SUPABASE_URL: Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY: Service role key (admin)
"""

import os
import sys
import re
from pathlib import Path

# Backend dizinini path'e ekle
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2-binary gerekli: pip install psycopg2-binary")
    sys.exit(1)

try:
    from supabase import create_client
except ImportError:
    print("❌ supabase gerekli: pip install supabase")
    sys.exit(1)


def slugify(text: str) -> str:
    """Türkçe karakterleri slug'a çevir"""
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    text = text.lower().translate(tr)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text).strip('-')
    return text[:80]


def get_database_url() -> str:
    """DATABASE_URL veya Supabase URL'den oluştur"""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        print("❌ SUPABASE_URL tanımlı değil (.env kontrol et)")
        sys.exit(1)

    # Supabase URL'den connection string oluştur
    # postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
    project_ref = supabase_url.replace("https://", "").replace("http://", "").split(".")[0]
    password = os.getenv("SUPABASE_DB_PASSWORD")
    region = os.getenv("SUPABASE_REGION", "aws-0-us-east-1")

    if not password:
        print("⚠️  SUPABASE_DB_PASSWORD tanımlı değil")
        print("    Supabase Dashboard → Settings → Database → Connection string'den alabilirsin")
        print("    Veya doğrudan DATABASE_URL tanımla")
        sys.exit(1)

    return f"postgresql://postgres.{project_ref}:{password}@{region}.pooler.supabase.com:6543/postgres"


def main():
    print("=" * 60)
    print("SLUG MİGRATİON — interviews tablosu")
    print("=" * 60)

    # 1. Supabase admin client
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_key:
        print("❌ SUPABASE_URL ve SUPABASE_SERVICE_ROLE_KEY gerekli")
        sys.exit(1)

    sb = create_client(supabase_url, service_key)

    # 2. DATABASE_URL ile slug kolonu ekle
    db_url = get_database_url()
    print(f"\n[1/3] PostgreSQL'e bağlanılıyor...")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()

        print("   + ALTER TABLE (slug kolonu ekle)")
        cur.execute("ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS slug TEXT")

        print("   + CREATE UNIQUE INDEX")
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_interviews_slug
            ON public.interviews(slug) WHERE slug IS NOT NULL
        """)

        print("   + NOTIFY pgrst, 'reload schema'")
        cur.execute("NOTIFY pgrst, 'reload schema'")

        cur.close()
        conn.close()
        print("   ✅ Şema güncellendi")
    except Exception as e:
        print(f"   ❌ SQL hatası: {e}")
        sys.exit(1)

    # 3. Mevcut soruları çek
    print(f"\n[2/3] Sorular çekiliyor...")
    try:
        result = sb.table("interviews").select("id, title, slug").execute()
        rows = result.data or []
        print(f"   + {len(rows)} soru bulundu")
    except Exception as e:
        print(f"   ❌ SELECT hatası: {e}")
        sys.exit(1)

    # 4. Slug üret + UPDATE
    print(f"\n[3/3] Slug üretiliyor + güncelleniyor...")
    seen = set()
    updated = 0
    skipped = 0
    errors = []

    for row in rows:
        title = row.get("title", "")
        existing = row.get("slug")
        if existing:
            skipped += 1
            seen.add(existing)
            continue

        new_slug = slugify(title)
        # Duplicate handling
        final_slug = new_slug
        counter = 1
        while final_slug in seen:
            counter += 1
            final_slug = f"{new_slug}-{counter}"
        seen.add(final_slug)

        try:
            sb.table("interviews").update({"slug": final_slug}).eq("id", row["id"]).execute()
            updated += 1
            if updated <= 5 or updated % 10 == 0:
                print(f"   + #{row['id']}: {title[:30]} → {final_slug}")
        except Exception as e:
            errors.append({"id": row["id"], "title": title, "error": str(e)})

    print("\n" + "=" * 60)
    print(f"TAMAMLANDI")
    print(f"   Toplam: {len(rows)}")
    print(f"   Güncellenen: {updated}")
    print(f"   Atlanan (zaten slug var): {skipped}")
    print(f"   Hata: {len(errors)}")
    if errors:
        for err in errors[:3]:
            print(f"     ! #{err['id']}: {err['error']}")
    print("=" * 60)


if __name__ == "__main__":
    main()