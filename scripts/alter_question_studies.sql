-- scripts/alter_question_studies.sql
-- question_studies tablosuna SEO metadata kolonları ekle.
-- Idempotent: her ALTER IF EXISTS/IF NOT EXISTS ile çalıştırılabilir.
--
-- Mevcut: id, question_id, problem_understanding, approach_1-3 (title/code/complexity),
--         challenges, related_question_ids, updated_at
--
-- Eklenen: study_slug (UNIQUE), seo_title, seo_description, keywords TEXT[],
--          category, level, estimated_read_time_min, prereq_topics,
--          difficulty_progression

BEGIN;

-- study_slug: URL-friendly identifier
ALTER TABLE public.question_studies
    ADD COLUMN IF NOT EXISTS study_slug TEXT;

-- UNIQUE constraint (idempotent — var mı bak)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'question_studies_study_slug_key'
    ) THEN
        ALTER TABLE public.question_studies
            ADD CONSTRAINT question_studies_study_slug_key UNIQUE (study_slug);
    END IF;
END $$;

-- SEO title — meta tag ve OG için
ALTER TABLE public.question_studies
    ADD COLUMN IF NOT EXISTS seo_title TEXT;

-- SEO description (<160 char)
ALTER TABLE public.question_studies
    ADD COLUMN IF NOT EXISTS seo_description TEXT;

-- Keywords dizisi — meta keywords + JSON-LD
ALTER TABLE public.question_studies
    ADD COLUMN IF NOT EXISTS keywords TEXT[] DEFAULT '{}';

-- Kategori ve seviye (CSV metadata'sı)
ALTER TABLE public.question_studies
    ADD COLUMN IF NOT EXISTS category TEXT;

ALTER TABLE public.question_studies
    ADD COLUMN IF NOT EXISTS level TEXT;

-- Schema.org timeRequired için okuma süresi
ALTER TABLE public.question_studies
    ADD COLUMN IF NOT EXISTS estimated_read_time_min INT DEFAULT 8;

-- Ön koşullar
ALTER TABLE public.question_studies
    ADD COLUMN IF NOT EXISTS prereq_topics TEXT;

-- Zorluk akışı (ör. "önce temel DP bitir")
ALTER TABLE public.question_studies
    ADD COLUMN IF NOT EXISTS difficulty_progression TEXT;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_question_studies_study_slug
    ON public.question_studies (study_slug);

CREATE INDEX IF NOT EXISTS idx_question_studies_category
    ON public.question_studies (category);

CREATE INDEX IF NOT EXISTS idx_question_studies_level
    ON public.question_studies (level);

-- Updated_at trigger — content güncellenince otomatik NOW()
CREATE OR REPLACE FUNCTION public.touch_question_studies_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_question_studies_updated_at ON public.question_studies;
CREATE TRIGGER trg_question_studies_updated_at
    BEFORE UPDATE ON public.question_studies
    FOR EACH ROW
    EXECUTE FUNCTION public.touch_question_studies_updated_at();

COMMIT;

-- Schema reload for PostgREST
NOTIFY pgrst, 'reload schema';
