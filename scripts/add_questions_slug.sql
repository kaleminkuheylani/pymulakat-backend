-- scripts/add_questions_slug.sql
-- questions tablosuna slug column ekle. CSV-DB senkron.
--
-- ⚠️ MEMORY KURALI:
--  - questions tablosuna bir daha ALTER YAPILMAYACAK (column freeze)
--  - CSV = TEK kaynak (frontend), DB = arşiv
--  - title ve slug AYRI column'lar (function üretmez, manuel atanır)
--  - CSV ve DB her zaman senkron olmalı
--  - Sadece Supabase SQL Editor'de çalıştır (ASLA Railway)
--
-- 📋 Bu script idempotent. Birden fazla çalıştırılabilir.

BEGIN;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 1) Slug column ekle (idempotent)                                   ║
-- ╚═══════════════════════════════════════════════════════════════════╝

ALTER TABLE public.questions
    ADD COLUMN IF NOT EXISTS slug TEXT;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 2) UNIQUE constraint (idempotent)                                 ║
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
-- ║ 3) Index (idempotent)                                              ║
-- ╚═══════════════════════════════════════════════════════════════════╝

CREATE INDEX IF NOT EXISTS idx_questions_slug
    ON public.questions (slug);

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 4) Slug değerlerini manuel ata (CSV'deki title ile senkron)      ║
-- ║                                                                    ║
-- ║ Her satır için slug, title'dan türetilmiş ama function DEĞİL,     ║
-- ║ manuel atama yapılır. Böylece:                                     ║
-- ║  - title değişirse slug'ı da bilinçli güncelleriz                ║
-- ║  - DB'de slug tahmin yürütmez                                     ║
-- ║  - CSV-FIRST mimariye tam uyum                                    ║
-- ║                                                                    ║
-- ║ CSV'deki title ile slug eşleşmesi:                                ║
-- ║  id=127: 'DataFrame Satır Normalizasyonu'                          ║
-- ║  id=130: 'DataFrame NaN Doldurma'                                  ║
-- ║  id=139: 'DataFrame NaN Sayımı'                                    ║
-- ║  diğer 139 satır: title'dan slug (CSV ile senkron)                ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- ── Collision çözümü (id=127/130/139) ─────────────────────
UPDATE public.questions SET slug = 'dataframe-satir-normalizasyonu' WHERE id = 127;
UPDATE public.questions SET slug = 'dataframe-nan-doldurma'         WHERE id = 130;
UPDATE public.questions SET slug = 'dataframe-nan-sayimi'           WHERE id = 139;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 5) Manuel slug atanmamış satırları raporla                        ║
-- ║    Hangi id'lerin hâlâ slug'ı NULL? Bunlar elle atanmalı.        ║
-- ╚═══════════════════════════════════════════════════════════════════╝

DO $$
DECLARE
    null_count INT;
BEGIN
    SELECT COUNT(*) INTO null_count
    FROM public.questions
    WHERE slug IS NULL;

    IF null_count > 0 THEN
        RAISE WARNING '⚠ % satırın slug''ı hâlâ NULL. Manuel atama gerekli.', null_count;
    ELSE
        RAISE NOTICE '✓ Tüm slug dolu';
    END IF;
END $$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 6) Collision kontrolü                                              ║
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
        RAISE EXCEPTION '❌ % duplicate slug var!', dup_count;
    ELSE
        RAISE NOTICE '✓ Slug collision yok';
    END IF;
END $$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 7) NOT NULL constraint                                            ║
-- ║    ⚠️ Bu adım sadece TÜM slug doluysa çalışır.                   ║
-- ║    Eğer adım 5 NULL raporladıysa, önce manuel atama yap.        ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- Bu adımı güvenli yapmak için slug NULL olan varsa atla
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM public.questions WHERE slug IS NULL) THEN
        RAISE WARNING '⚠ NOT NULL constraint atlanadı — slug NULL var. Manuel atama gerekli.';
    ELSE
        ALTER TABLE public.questions ALTER COLUMN slug SET NOT NULL;
        RAISE NOTICE '✓ NOT NULL constraint eklendi';
    END IF;
END $$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 8) Schema reload (PostgREST)                                      ║
-- ╚═══════════════════════════════════════════════════════════════════╝

NOTIFY pgrst, 'reload schema';

COMMIT;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ DOĞRULAMA                                                          ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- NULL slug'lar (manuel atama gerek)
-- SELECT id, title FROM public.questions WHERE slug IS NULL;

-- Collision row'lar
-- SELECT id, title, slug FROM public.questions WHERE id IN (127, 130, 139);

-- Collision kontrolü
-- SELECT slug, COUNT(*) FROM public.questions
-- GROUP BY slug HAVING COUNT(*) > 1;

-- Schema
-- SELECT column_name, is_nullable, data_type
--   FROM information_schema.columns
--  WHERE table_name = 'questions' AND column_name = 'slug';

-- ⚠️ ROLLBACK:
-- ALTER TABLE public.questions DROP CONSTRAINT IF EXISTS questions_slug_key;
-- DROP INDEX IF EXISTS idx_questions_slug;
-- ALTER TABLE public.questions DROP COLUMN IF EXISTS slug;
