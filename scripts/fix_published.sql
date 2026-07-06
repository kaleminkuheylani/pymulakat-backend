-- FIX: questions tablosunda is_published ekle + tümünü aktif yap
-- Sorun: API is_published=true filtreliyor, ama DB'de bu sütun yok / false
-- Tek sorguda çözüm

DO $$
BEGIN
    -- 1) Kolon yoksa ekle
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'questions' 
          AND column_name = 'is_published'
          AND table_schema = 'public'
    ) THEN
        ALTER TABLE public.questions 
        ADD COLUMN is_published BOOLEAN NOT NULL DEFAULT true;
        RAISE NOTICE 'is_published kolonu eklendi (default true)';
    ELSE
        RAISE NOTICE 'is_published kolonu zaten var';
    END IF;
END $$;

-- 2) Hepsini aktif yap
UPDATE public.questions 
SET is_published = true 
WHERE is_published IS NULL OR is_published = false;

-- 3) Doğrulama
SELECT 
    COUNT(*) FILTER (WHERE is_published = true) AS active,
    COUNT(*) FILTER (WHERE is_published = false) AS inactive,
    COUNT(*) AS total
FROM public.questions;