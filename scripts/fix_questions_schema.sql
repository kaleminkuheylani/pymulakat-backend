-- ═══════════════════════════════════════════════════════════
-- FIX: public.questions tablosu şema drift düzeltme
-- ═══════════════════════════════════════════════════════════
-- Tarih: 2026-07-08
-- Neden: Production'da `source_id` kolonu yok (PGRST204 hatası).
--        migrate_questions.sql ilk deploy'da tam çalışmamış olabilir.
--
-- Bu SQL idempotent — birden fazla çalıştırmak güvenli.
-- Railway shell'de: `psql $DATABASE_URL -f scripts/fix_questions_schema.sql`

-- 1) Eğer tablo yoksa tam şemayla oluştur
CREATE TABLE IF NOT EXISTS public.questions (
  id BIGSERIAL PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  source_id INTEGER,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  explanation TEXT,
  complexity TEXT,
  level TEXT NOT NULL,
  category TEXT NOT NULL,
  function_name TEXT,
  function_signature TEXT,
  starter_code TEXT,
  test_cases JSONB NOT NULL DEFAULT '[]'::jsonb,
  hints JSONB NOT NULL DEFAULT '[]'::jsonb,
  related_concepts TEXT[] DEFAULT '{}',
  related_question_ids BIGINT[] DEFAULT '{}',
  tags TEXT[] DEFAULT '{}',
  is_published BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2) Eksik kolonları idempotent ekle (kolon zaten varsa no-op)
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS slug TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS source_id INTEGER;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS explanation TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS complexity TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS level TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS function_name TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS function_signature TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS starter_code TEXT;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS test_cases JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS hints JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS related_concepts TEXT[] DEFAULT '{}';
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS related_question_ids BIGINT[] DEFAULT '{}';
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS is_published BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- 3) NULL olamaz alanlar için DEFAULT koy (geriye uyumlu)
UPDATE public.questions SET description = '' WHERE description IS NULL;
UPDATE public.questions SET title = '' WHERE title IS NULL;
UPDATE public.questions SET level = 'beginner' WHERE level IS NULL;
UPDATE public.questions SET category = 'python-basics' WHERE category IS NULL;
UPDATE public.questions SET slug = 'q-' || id::text WHERE slug IS NULL;

-- 4) Index/constraint'ler
CREATE UNIQUE INDEX IF NOT EXISTS idx_questions_slug ON public.questions(slug);
CREATE UNIQUE INDEX IF NOT EXISTS idx_questions_source_id ON public.questions(source_id);
CREATE INDEX IF NOT EXISTS idx_questions_category ON public.questions(category) WHERE is_published = true;
CREATE INDEX IF NOT EXISTS idx_questions_level ON public.questions(level) WHERE is_published = true;
CREATE INDEX IF NOT EXISTS idx_questions_published ON public.questions(is_published, created_at DESC);

-- 5) updated_at trigger
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_questions_updated_at ON public.questions;
CREATE TRIGGER trg_questions_updated_at
  BEFORE UPDATE ON public.questions
  FOR EACH ROW
  EXECUTE FUNCTION public.set_updated_at();

-- 6) RLS — public read, service_role write
ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Questions public read" ON public.questions;
CREATE POLICY "Questions public read"
  ON public.questions
  FOR SELECT
  USING (is_published = true);

-- 7) PostgREST schema cache invalidate (KRİTİK!)
NOTIFY pgrst, 'reload schema';

-- 8) Doğrulama — kolonların varlığını ve sayılarını raporla
SELECT
  COUNT(*) AS total_rows,
  COUNT(source_id) AS rows_with_source_id,
  COUNT(slug) AS rows_with_slug,
  COUNT(category) AS rows_with_category
FROM public.questions;

-- Schema cache reload doğrulaması
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'questions'
ORDER BY ordinal_position;
