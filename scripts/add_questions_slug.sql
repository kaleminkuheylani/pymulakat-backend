-- scripts/add_questions_slug.sql
-- questions tablosuna slug column geri ekle.
--
-- ⚠️ MEMORY KURALI: Column freeze! Bu migration SADECE kullanıcı isteği üzerine
-- yapılıyor (kullanıcı "questions olarak değiştir" dedi). Bir daha bu column
-- dışında ekleme YAPILMAYACAK.
--
-- 📋 ÇALIŞTIRMA SIRASI (Supabase SQL Editor):
--  1) ÖNCE: scripts/slugify_title.sql    (function oluştur)
--  2) SONRA: scripts/add_questions_slug.sql  (bu dosya — column + UPDATE)
--
-- ⚠️ DEPLOYMENT: Bu SQL ASLA Railway üzerinden çalıştırılmaz.
-- Sadece Supabase Dashboard → SQL Editor'de kullanıcı elle çalıştırır.
-- Railway sadece API deploy eder, migration yapmaz.
--
-- Önceki commit (e112938) yanlış tablo adıyla (interviews) yazılmıştı.
-- Doğru tablo: public.questions
--
-- ⚠️ BU MIGRATION TEK SEFERLİK:
-- - Çalıştır, doğrula, bir daha bu tabloya ALTER yapma.

BEGIN;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 1) Slug column ekle                                                ║
-- ╚═══════════════════════════════════════════════════════════════════╝

ALTER TABLE public.questions
    ADD COLUMN IF NOT EXISTS slug TEXT;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 2) UNIQUE constraint                                               ║
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
-- ║ 3) Index (slug lookup için)                                       ║
-- ╚═══════════════════════════════════════════════════════════════════╝

CREATE INDEX IF NOT EXISTS idx_questions_slug
    ON public.questions (slug);

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 4) Mevcut satırları doldur (slugify_title ile)                    ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- NULL olan tüm slug'ları title'dan üret
UPDATE public.questions
SET slug = public.slugify_title(title)
WHERE slug IS NULL OR slug = '';

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 5) Slug collision kontrolü (nadir ama mümkün)                    ║
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
-- ║ 6) NOT NULL constraint (güvenlik)                                 ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- NOT NULL eklemek için önce tüm satırlarda dolu olmalı
-- (yukarıdaki UPDATE ile dolu)
ALTER TABLE public.questions
    ALTER COLUMN slug SET NOT NULL;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 7) Schema reload (PostgREST)                                      ║
-- ╚═══════════════════════════════════════════════════════════════════╝

NOTIFY pgrst, 'reload schema';

COMMIT;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ DOĞRULAMA                                                          ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- SELECT id, title, slug FROM public.questions ORDER BY id LIMIT 5;
-- Beklenen:
--  1 | Two Sum            | two-sum
--  2 | Fibonacci          | fibonacci
--  3 | 0/1 Knapsack       | 01-knapsack
--  ...

-- SELECT COUNT(*) AS total, COUNT(slug) AS with_slug FROM public.questions;
-- Beklenen: total == with_slug (hepsi dolu)

-- SELECT slug, COUNT(*) FROM public.questions GROUP BY slug HAVING COUNT(*) > 1;
-- Beklenen: 0 satır (collision yok)

-- SELECT column_name, is_nullable, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'questions' AND column_name = 'slug';
-- Beklenen: is_nullable = 'NO', data_type = 'text'

-- ⚠️ ROLLBACK (GEREKEKSE):
-- ALTER TABLE public.questions DROP CONSTRAINT IF EXISTS questions_slug_key;
-- DROP INDEX IF EXISTS idx_questions_slug;
-- ALTER TABLE public.questions DROP COLUMN IF EXISTS slug;
