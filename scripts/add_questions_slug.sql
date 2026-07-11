-- scripts/add_questions_slug.sql
-- questions tablosuna slug column ekle, DB'deki title'dan slugify et.
-- CSV'YE DOKUNMA. Sadece Supabase SQL Editor'de çalıştır.
--
-- ⚠️ MEMORY KURALI:
--  - questions tablosuna bir daha ALTER YAPILMAYACAK
--  - CSV = TEK kaynak (frontend), DB = arşiv
--  - Sadece Supabase SQL Editor'de çalıştır, ASLA Railway
--
-- 📋 Bu script idempotent: birden fazla çalıştırılabilir.

BEGIN;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 1) slugify_title() FUNCTION                                       ║
-- ║    DB'deki title'dan URL-friendly slug üretir.                    ║
-- ║    Frontend lib/questionMeta.ts:slugifyTitle() ile uyumlu.        ║
-- ╚═══════════════════════════════════════════════════════════════════╝

CREATE OR REPLACE FUNCTION public.slugify_title(input TEXT)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
PARALLEL SAFE
AS $$
DECLARE
    s TEXT;
BEGIN
    IF input IS NULL OR input = '' THEN
        RETURN '';
    END IF;

    s := LOWER(input);

    -- Türkçe karakterler
    s := REPLACE(s, 'ı', 'i'); s := REPLACE(s, 'İ', 'i');
    s := REPLACE(s, 'ş', 's'); s := REPLACE(s, 'Ş', 's');
    s := REPLACE(s, 'ç', 'c'); s := REPLACE(s, 'Ç', 'c');
    s := REPLACE(s, 'ğ', 'g'); s := REPLACE(s, 'Ğ', 'g');
    s := REPLACE(s, 'ö', 'o'); s := REPLACE(s, 'Ö', 'o');
    s := REPLACE(s, 'ü', 'u'); s := REPLACE(s, 'Ü', 'u');

    -- Apostrof/tırnak kaldır
    s := REPLACE(s, '''', '');
    s := REPLACE(s, '"', '');
    s := REPLACE(s, '`', '');

    -- Non-alphanumeric (boşluk/tire hariç) kaldır
    s := REGEXP_REPLACE(s, '[^a-z0-9\s-]', '', 'g');

    -- Çoklu boşluk/tire → tek tire
    s := REGEXP_REPLACE(s, '\s+', '-', 'g');
    s := REGEXP_REPLACE(s, '-+', '-', 'g');

    -- Baştaki/sondaki tire kırp
    s := TRIM(BOTH '-' FROM s);

    RETURN s;
END;
$$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 2) Slug column ekle (idempotent)                                   ║
-- ╚═══════════════════════════════════════════════════════════════════╝

ALTER TABLE public.questions
    ADD COLUMN IF NOT EXISTS slug TEXT;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 3) UNIQUE constraint (idempotent)                                 ║
-- ╚═══════════════════════════════════════════════════════════════════╝

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'questions_slug_key'
    ) THEN
        ALTER TABLE public.questions
            ADD CONSTRAINT questions_slug_key UNIQUE (slug);
    END IF;
END $$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 4) Index (idempotent)                                              ║
-- ╚═══════════════════════════════════════════════════════════════════╝

CREATE INDEX IF NOT EXISTS idx_questions_slug
    ON public.questions (slug);

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 5) Slug NULL olanları title'dan üret (DB'deki title ile)          ║
-- ║    Bu adım collision'ları ortaya çıkarır.                         ║
-- ╚═══════════════════════════════════════════════════════════════════╝

UPDATE public.questions
SET slug = public.slugify_title(title)
WHERE slug IS NULL OR slug = '';

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 6) Collision raporu (bilgi amaçlı)                                ║
-- ║    Hangi id'lerin title'ı çakışıyor gösterir.                    ║
-- ╚═══════════════════════════════════════════════════════════════════╝

DO $$
DECLARE
    dup_record RECORD;
BEGIN
    FOR dup_record IN
        SELECT id, title, slug
        FROM public.questions
        WHERE slug IN (
            SELECT slug FROM public.questions
            WHERE slug IS NOT NULL
            GROUP BY slug
            HAVING COUNT(*) > 1
        )
        ORDER BY slug, id
    LOOP
        RAISE NOTICE 'COLLISION: id=%, title=%, slug=%',
            dup_record.id, dup_record.title, dup_record.slug;
    END LOOP;
END $$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 7) Collision çözümü: DB'deki title'ı güncelle (CSV DOKUNULMAZ)   ║
-- ║    id=127/130/139 hepsi 'DataFrame\' → anlamlı title'lar         ║
-- ║    CSV'Yİ ETKİLEMEZ. Sadece DB'deki title rename + slug yenile.  ║
-- ╚═══════════════════════════════════════════════════════════════════╝

UPDATE public.questions SET title = 'DataFrame Satır Normalizasyonu' WHERE id = 127;
UPDATE public.questions SET title = 'DataFrame NaN Doldurma'         WHERE id = 130;
UPDATE public.questions SET title = 'DataFrame NaN Sayımı'           WHERE id = 139;

-- Slug'ları yeni title'dan yeniden üret (collision row'lar)
UPDATE public.questions SET slug = 'dataframe-satir-normalizasyonu' WHERE id = 127;
UPDATE public.questions SET slug = 'dataframe-nan-doldurma'         WHERE id = 130;
UPDATE public.questions SET slug = 'dataframe-nan-sayimi'           WHERE id = 139;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 8) Final collision kontrolü (RAISE EXCEPTION hâlâ varsa)          ║
-- ╚═══════════════════════════════════════════════════════════════════╝

DO $$
DECLARE
    dup_count INT;
BEGIN
    SELECT COUNT(*) INTO dup_count
    FROM (
        SELECT slug, COUNT(*) c
        FROM public.questions
        WHERE slug IS NOT NULL
        GROUP BY slug
        HAVING COUNT(*) > 1
    ) t;

    IF dup_count > 0 THEN
        RAISE EXCEPTION '❌ HÂLÂ % duplicate slug var!', dup_count;
    ELSE
        RAISE NOTICE '✓ Tüm slug unique';
    END IF;
END $$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 9) NOT NULL constraint (tüm slug dolu, güvenli)                   ║
-- ╚═══════════════════════════════════════════════════════════════════╝

ALTER TABLE public.questions
    ALTER COLUMN slug SET NOT NULL;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 10) Schema reload (PostgREST)                                     ║
-- ╚═══════════════════════════════════════════════════════════════════╝

NOTIFY pgrst, 'reload schema';

COMMIT;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ DOĞRULAMA                                                          ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- 1) Toplam + dolu say
-- SELECT COUNT(*) total, COUNT(slug) with_slug FROM public.questions;
-- Beklenen: total == with_slug

-- 2) Collision row'lar
-- SELECT id, title, slug FROM public.questions
-- WHERE id IN (127, 130, 139);

-- 3) Collision kontrolü (0 satır olmalı)
-- SELECT slug, COUNT(*) FROM public.questions
-- GROUP BY slug HAVING COUNT(*) > 1;

-- 4) Schema bilgisi
-- SELECT column_name, is_nullable, data_type
--   FROM information_schema.columns
--  WHERE table_name = 'questions' AND column_name = 'slug';
-- Beklenen: NOT NULL, text

-- ⚠️ ROLLBACK (gerekirse):
-- ALTER TABLE public.questions DROP CONSTRAINT IF EXISTS questions_slug_key;
-- DROP INDEX IF EXISTS idx_questions_slug;
-- ALTER TABLE public.questions DROP COLUMN IF EXISTS slug;
-- DROP FUNCTION IF EXISTS public.slugify_title(TEXT);
-- (Title rename'leri geri almak istersen: yedekten veya commit'ten önceki title'lar)
