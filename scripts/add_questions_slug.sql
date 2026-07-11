-- scripts/add_questions_slug.sql
-- questions tablosuna slug column geri ekle (slugify_title dahili).
--
-- ⚠️ MEMORY KURALI: Column freeze! Bu migration SADECE kullanıcı isteği üzerine.
-- Bir daha questions tablosuna ALTER YAPILMAYACAK.
--
-- ⚠️ DEPLOYMENT: ASLA Railway üzerinden çalıştırılmaz. Sadece Supabase
-- SQL Editor'de kullanıcı elle çalıştırır.
--
-- 📋 TEK DOSYA: slugify_title() function + column ekleme tek transaction'da.
-- Supabase SQL Editor'de sadece bu dosyayı çalıştırman yeterli.

BEGIN;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 1) slugify_title() FUNCTION (slug üretici)                       ║
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

    s := input;

    -- 1) Lowercase
    s := LOWER(s);

    -- 2) Türkçe karakter → ASCII
    s := REPLACE(s, 'ı', 'i');
    s := REPLACE(s, 'İ', 'i');
    s := REPLACE(s, 'ş', 's');
    s := REPLACE(s, 'Ş', 's');
    s := REPLACE(s, 'ç', 'c');
    s := REPLACE(s, 'Ç', 'c');
    s := REPLACE(s, 'ğ', 'g');
    s := REPLACE(s, 'Ğ', 'g');
    s := REPLACE(s, 'ö', 'o');
    s := REPLACE(s, 'Ö', 'o');
    s := REPLACE(s, 'ü', 'u');
    s := REPLACE(s, 'Ü', 'u');

    -- 3) Apostrof ve tırnak kaldır (TİRE DEĞİL)
    s := REPLACE(s, '''', '');
    s := REPLACE(s, '"', '');
    s := REPLACE(s, '`', '');

    -- 4) Non-alphanumeric (boşluk/tire hariç) kaldır
    s := REGEXP_REPLACE(s, '[^a-z0-9\s-]', '', 'g');

    -- 5) Çoklu boşluk → tire
    s := REGEXP_REPLACE(s, '\s+', '-', 'g');
    s := REGEXP_REPLACE(s, '-+', '-', 'g');

    -- 6) Baştaki/sondaki tire kırp
    s := TRIM(BOTH '-' FROM s);

    RETURN s;
END;
$$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 2) Slug column ekle                                                ║
-- ╚═══════════════════════════════════════════════════════════════════╝

ALTER TABLE public.questions
    ADD COLUMN IF NOT EXISTS slug TEXT;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 3) UNIQUE constraint                                               ║
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
-- ║ 4) Index (slug lookup için)                                       ║
-- ╚═══════════════════════════════════════════════════════════════════╝

CREATE INDEX IF NOT EXISTS idx_questions_slug
    ON public.questions (slug);

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 5) Mevcut satırları doldur (slugify_title ile)                    ║
-- ╚═══════════════════════════════════════════════════════════════════╝

UPDATE public.questions
SET slug = public.slugify_title(title)
WHERE slug IS NULL OR slug = '';

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 5b) Collision düzeltme (DataFrame x3 — title değiştirildi)        ║
-- ║     CSV düzeltmesi commit'i ile senkron.                          ║
-- ╚═══════════════════════════════════════════════════════════════════╝

UPDATE public.questions SET slug = 'dataframe-satir-normalizasyonu' WHERE id = 127 AND slug = 'dataframe';
UPDATE public.questions SET slug = 'dataframe-nan-doldurma'         WHERE id = 130 AND slug = 'dataframe';
UPDATE public.questions SET slug = 'dataframe-nan-sayimi'           WHERE id = 139 AND slug = 'dataframe';

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 6) Slug collision kontrolü                                        ║
-- ╚═══════════════════════════════════════════════════════════════════╝

DO $$
DECLARE
    dup_count INT;
BEGIN
    SELECT COUNT(*) INTO dup_count
    FROM (
        SELECT slug, COUNT(*) as c
        FROM public.questions
        WHERE slug IS NOT NULL
        GROUP BY slug
        HAVING COUNT(*) > 1
    ) t;

    IF dup_count > 0 THEN
        RAISE WARNING 'Slug collision: % duplicate slug(lar) bulundu. '
                      'Bunlar manuel -2, -3 suffix ile çözülmeli.', dup_count;
    ELSE
        RAISE NOTICE '✓ Slug collision yok — tüm slug unique';
    END IF;
END $$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 7) NOT NULL constraint                                            ║
-- ╚═══════════════════════════════════════════════════════════════════╝

ALTER TABLE public.questions
    ALTER COLUMN slug SET NOT NULL;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 8) Schema reload (PostgREST)                                      ║
-- ╚═══════════════════════════════════════════════════════════════════╝

NOTIFY pgrst, 'reload schema';

COMMIT;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ DOĞRULAMA (çalıştır, sonuçları kontrol et)                       ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- SELECT id, title, slug FROM public.questions ORDER BY id LIMIT 5;
-- SELECT COUNT(*) AS total, COUNT(slug) AS with_slug FROM public.questions;
-- SELECT slug, COUNT(*) FROM public.questions GROUP BY slug HAVING COUNT(*) > 1;
-- SELECT column_name, is_nullable, data_type
--   FROM information_schema.columns
--  WHERE table_name = 'questions' AND column_name = 'slug';

-- ⚠️ ROLLBACK (gerekirse):
-- ALTER TABLE public.questions DROP CONSTRAINT IF EXISTS questions_slug_key;
-- DROP INDEX IF EXISTS idx_questions_slug;
-- ALTER TABLE public.questions DROP COLUMN IF EXISTS slug;
-- DROP FUNCTION IF EXISTS public.slugify_title(TEXT);
