-- ═══════════════════════════════════════════════════════════
-- INTERWIEWS TABLOSUNA YENİ KOLONLAR EKLE
-- Eski şema + yeni SEO alanları birlikte
-- IDEMPOTENT — IF NOT EXISTS ile birden fazla çalıştırılabilir
-- ═══════════════════════════════════════════════════════════

-- 1. slug (URL-friendly identifier)
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS slug TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_interwiews_slug ON public.interwiews(slug);

-- 2. SEO alanları
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS explanation TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS complexity TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS related_concepts TEXT[] DEFAULT '{}';
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS related_question_ids BIGINT[] DEFAULT '{}';
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS tutorial_slug TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS meta_title TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS meta_description TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS meta_keywords TEXT[] DEFAULT '{}';
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS reading_time_minutes INT DEFAULT 5;

-- 3. hints (önceden olmayabilir)
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS hints TEXT[] DEFAULT '{}';

-- 4. function_name + starter_code (zaten olmalı ama yoksa)
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS function_name TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS starter_code TEXT;

-- 5. updated_at trigger
DROP TRIGGER IF EXISTS trg_interwiews_updated ON public.interwiews;
CREATE TRIGGER trg_interwiews_updated
  BEFORE UPDATE ON public.interwiews
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- 6. Doğrulama — yeni kolonları listele
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'interwiews'
ORDER BY ordinal_position;