-- scripts/add_questions_slug.sql
-- questions tablosuna slug column geri ekle (slugify_title dahili).
--
-- ⚠️ MEMORY KURALI: Column freeze! Bu migration TEK SEFERLİK.
-- questions tablosuna bir daha ALTER YAPILMAYACAK.
--
-- ⚠️ DEPLOYMENT: ASLA Railway. Sadece Supabase SQL Editor (kullanıcı elle).
--
-- 📋 TEK DOSYA — Supabase SQL Editor'de sadece bunu çalıştır.

BEGIN;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 1) slugify_title() FUNCTION                                       ║
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

    -- Apostrof kaldır
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
-- ║ 4) Index                                                           ║
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
-- ║ 6) Collision çözümü (DataFrame x3 — kullanıcı onayı ile)         ║
-- ║                                                                    ║
-- ║ 3 soru aynı title 'DataFrame\'a sahip. CSV title değiştirildiği  ║
-- ║ için bu satırlara manuel slug atandı. id=127/130/139.            ║
-- ║                                                                    ║
-- ║ Idempotent: AND slug = 'dataframe' koşulu, zaten düzeltilmişse   ║
-- ║ etki etmez.                                                        ║
-- ╚═══════════════════════════════════════════════════════════════════╝

UPDATE public.questions SET slug = 'dataframe-satir-normalizasyonu' WHERE id = 127 AND slug = 'dataframe';
UPDATE public.questions SET slug = 'dataframe-nan-doldurma'         WHERE id = 130 AND slug = 'dataframe';
UPDATE public.questions SET slug = 'dataframe-nan-sayimi'           WHERE id = 139 AND slug = 'dataframe';

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 7) Collision kontrolü (final)                                      ║
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
        RAISE EXCEPTION '❌ HÂLÂ % duplicate slug var! Manuel çöz gerekli.', dup_count;
    ELSE
        RAISE NOTICE '✓ Tüm slug unique — collision yok';
    END IF;
END $$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 8) NOT NULL constraint                                            ║
-- ╚═══════════════════════════════════════════════════════════════════╝

ALTER TABLE public.questions
    ALTER COLUMN slug SET NOT NULL;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 9) Schema reload (PostgREST)                                      ║
-- ╚═══════════════════════════════════════════════════════════════════╝

NOTIFY pgrst, 'reload schema';

COMMIT;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ DOĞRULAMA                                                          ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- SELECT id, title, slug FROM public.questions ORDER BY id LIMIT 5;
-- SELECT id, title, slug FROM public.questions WHERE id IN (127, 130, 139);
-- SELECT COUNT(*) total, COUNT(slug) with_slug FROM public.questions;
-- SELECT slug, COUNT(*) FROM public.questions GROUP BY slug HAVING COUNT(*) > 1;
-- SELECT column_name, is_nullable, data_type
--   FROM information_schema.columns
--  WHERE table_name = 'questions' AND column_name = 'slug';

-- ⚠️ ROLLBACK:
-- ALTER TABLE public.questions DROP CONSTRAINT IF EXISTS questions_slug_key;
-- DROP INDEX IF EXISTS idx_questions_slug;
-- ALTER TABLE public.questions DROP COLUMN IF EXISTS slug;
-- DROP FUNCTION IF EXISTS public.slugify_title(TEXT);
