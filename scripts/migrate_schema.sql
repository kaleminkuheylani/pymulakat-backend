-- ═══════════════════════════════════════════════════════════
-- BULK SCHEMA MIGRATION — tüm kolonları garantiye al
-- ═══════════════════════════════════════════════════════════

-- Temel kolonlar
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS id BIGINT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS level TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS topic TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS starter_code TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS function_name TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS test_cases JSONB DEFAULT '[]'::jsonb;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS hints TEXT[] DEFAULT '{}';
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- SEO kolonları
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS slug TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS explanation TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS complexity TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS related_concepts TEXT[] DEFAULT '{}';
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS related_question_ids BIGINT[] DEFAULT '{}';
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS tutorial_slug TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS meta_title TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS meta_description TEXT;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS meta_keywords TEXT[] DEFAULT '{}';
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS reading_time_minutes INT DEFAULT 5;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS view_count BIGINT DEFAULT 0;
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS attempt_count BIGINT DEFAULT 0;

-- Zaman damgaları
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE public.interwiews ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_interwiews_slug ON public.interwiews(slug);
CREATE INDEX IF NOT EXISTS idx_interwiews_category ON public.interwiews(category);
CREATE INDEX IF NOT EXISTS idx_interwiews_level ON public.interwiews(level);
CREATE INDEX IF NOT EXISTS idx_interwiews_tutorial ON public.interwiews(tutorial_slug) WHERE tutorial_slug IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_interwiews_tags ON public.interwiews USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_interwiews_concepts ON public.interwiews USING GIN(related_concepts);

-- PostgREST cache invalidate
NOTIFY pgrst, 'reload schema';

-- Doğrulama
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'interwiews'
ORDER BY ordinal_position;