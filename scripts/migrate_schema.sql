-- ═══════════════════════════════════════════════════════════
-- BULK SCHEMA MIGRATION — tüm kolonları garantiye al
-- ═══════════════════════════════════════════════════════════

-- Temel kolonlar
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS id BIGINT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS level TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS topic TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS starter_code TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS function_name TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS test_cases JSONB DEFAULT '[]'::jsonb;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS hints TEXT[] DEFAULT '{}';
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- SEO kolonları
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS slug TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS explanation TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS complexity TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS related_concepts TEXT[] DEFAULT '{}';
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS related_question_ids BIGINT[] DEFAULT '{}';
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS tutorial_slug TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS meta_title TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS meta_description TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS meta_keywords TEXT[] DEFAULT '{}';
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS reading_time_minutes INT DEFAULT 5;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS view_count BIGINT DEFAULT 0;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS attempt_count BIGINT DEFAULT 0;

-- Zaman damgaları
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_questions_slug ON public.questions(slug);
CREATE INDEX IF NOT EXISTS idx_questions_category ON public.questions(category);
CREATE INDEX IF NOT EXISTS idx_questions_level ON public.questions(level);
CREATE INDEX IF NOT EXISTS idx_questions_tutorial ON public.questions(tutorial_slug) WHERE tutorial_slug IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_questions_tags ON public.questions USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_questions_concepts ON public.questions USING GIN(related_concepts);

-- PostgREST cache invalidate
NOTIFY pgrst, 'reload schema';

-- Doğrulama
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'questions'
ORDER BY ordinal_position;