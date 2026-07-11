-- scripts/add_interviews_slug.sql
-- interviews tablosuna slug column'u geri ekle.
--
-- ⚠️ MEMORY KURALI: Column freeze! Bu migration SADECE kullanıcı isteği üzerine
-- yapılıyor (kullanıcı "slug alanını yanlışlıkla silmişim" dedi). Bir daha
-- bu column dışında ekleme YAPILMAYACAK.
--
-- Sebep: slug, URL routing için kritik (/interviews/{cat}/{slug}).
-- slugify_title() fonksiyonu (commit 3da65bc) bu column'u doldurmak için
-- kullanılacak.
--
-- ⚠️ BU MIGRATION TEK SEFERLİK:
-- - Çalıştır, doğrula, bir daha bu tabloya ALTER yapma.

BEGIN;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 1) Slug column ekle                                                ║
-- ╚═══════════════════════════════════════════════════════════════════╝

ALTER TABLE public.interviews
    ADD COLUMN IF NOT EXISTS slug TEXT;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 2) UNIQUE constraint                                               ║
-- ╚═══════════════════════════════════════════════════════════════════╝

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'interviews_slug_key'
    ) THEN
        ALTER TABLE public.interviews
            ADD CONSTRAINT interviews_slug_key UNIQUE (slug);
    END IF;
END $$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 3) Index (slug lookup için)                                       ║
-- ╚═══════════════════════════════════════════════════════════════════╝

CREATE INDEX IF NOT EXISTS idx_interviews_slug
    ON public.interviews (slug);

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 4) Mevcut satırları doldur (slugify_title ile)                    ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- NULL olan tüm slug'ları title'dan üret
UPDATE public.interviews
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
        FROM public.interviews
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
ALTER TABLE public.interviews
    ALTER COLUMN slug SET NOT NULL;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 7) Schema reload (PostgREST)                                      ║
-- ╚═══════════════════════════════════════════════════════════════════╝

NOTIFY pgrst, 'reload schema';

COMMIT;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ DOĞRULAMA                                                          ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- SELECT id, title, slug FROM public.interviews ORDER BY id LIMIT 5;
-- Beklenen:
--  1 | Two Sum            | two-sum
--  2 | Fibonacci          | fibonacci
--  3 | 0/1 Knapsack       | 01-knapsack
--  ...

-- SELECT COUNT(*) AS total, COUNT(slug) AS with_slug FROM public.interviews;
-- Beklenen: total == with_slug (hepsi dolu)

-- SELECT slug, COUNT(*) FROM public.interviews GROUP BY slug HAVING COUNT(*) > 1;
-- Beklenen: 0 satır (collision yok)

-- ⚠️ ROLLBACK (GEREKEKSE):
-- ALTER TABLE public.interviews DROP CONSTRAINT IF EXISTS interviews_slug_key;
-- DROP INDEX IF EXISTS idx_interviews_slug;
-- ALTER TABLE public.interviews DROP COLUMN IF EXISTS slug;
