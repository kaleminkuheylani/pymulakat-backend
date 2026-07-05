-- Migration: questions tablosu (production-ready, QUESTIONS.py ile sync)
-- 2026-07-05
--
-- Mimari:
--   1. QUESTIONS.py -> DB'ye seed edilir (scripts/seed_questions.py)
--   2. Endpoint'ler önce DB'den okur
--   3. DB boşsa veya hata durumunda QUESTIONS.py fallback
--   4. Frontend aynı API contract'ı görür (değişiklik yok)

CREATE TABLE IF NOT EXISTS public.questions (
  id BIGSERIAL PRIMARY KEY,
  -- Canonical slug (URL'de kullanılacak, örn: 'palindrome-checker')
  slug TEXT UNIQUE NOT NULL,
  -- Backend QUESTIONS.py'deki orijinal ID (referans için)
  source_id INTEGER UNIQUE,
  -- Metadata
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  explanation TEXT,
  complexity TEXT,        -- 'O(n)', 'O(log n)' vs.
  level TEXT NOT NULL,     -- 'beginner' | 'intermediate' | 'advanced'
  category TEXT NOT NULL,  -- 'python-basics' | 'list-dict' | 'strings' | 'pandas' | 'algorithms' | 'sql' | 'oop'
  -- Function signature (kod analizi için)
  function_name TEXT,
  function_signature TEXT,
  starter_code TEXT,
  -- Test cases JSONB: [{input: ..., expected: ..., description: ...}, ...]
  test_cases JSONB NOT NULL DEFAULT '[]'::jsonb,
  -- Hints JSONB: ["💡 ipucu 1", "💡 ipucu 2", ...]
  hints JSONB NOT NULL DEFAULT '[]'::jsonb,
  -- Related concepts (SEO için)
  related_concepts TEXT[] DEFAULT '{}',
  related_question_ids BIGINT[] DEFAULT '{}',
  -- Tags
  tags TEXT[] DEFAULT '{}',
  -- Status
  is_published BOOLEAN NOT NULL DEFAULT true,
  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- İndeksler
CREATE INDEX IF NOT EXISTS idx_questions_slug ON public.questions(slug);
CREATE INDEX IF NOT EXISTS idx_questions_source_id ON public.questions(source_id);
CREATE INDEX IF NOT EXISTS idx_questions_category ON public.questions(category) WHERE is_published = true;
CREATE INDEX IF NOT EXISTS idx_questions_level ON public.questions(level) WHERE is_published = true;
CREATE INDEX IF NOT EXISTS idx_questions_published ON public.questions(is_published, created_at DESC);

-- Tam metin arama için (ileride)
CREATE INDEX IF NOT EXISTS idx_questions_title_trgm ON public.questions USING gin (title gin_trgm_ops);
-- (pg_trgm extension gerekli; yoksa skip)

-- updated_at otomatik güncelleme
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

-- RLS: herkes okuyabilsin (misafir), sadece service_role yazabilsin
ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Questions public read" ON public.questions;
CREATE POLICY "Questions public read"
  ON public.questions
  FOR SELECT
  USING (is_published = true);

-- INSERT/UPDATE/DELETE service_role üzerinden (RLS bypass)
-- (gerekirse ek INSERT policy auth.uid() ile)

-- Comment
COMMENT ON TABLE public.questions IS 'Python mülakat soruları. QUESTIONS.py kaynak, bu tablo production kopyası.';
COMMENT ON COLUMN public.questions.slug IS 'Canonical URL slug: /interviews/{category}/{slug}';
COMMENT ON COLUMN public.questions.source_id IS 'QUESTIONS.py ID referansı (debug için)';
COMMENT ON COLUMN public.questions.test_cases IS 'JSON array: [{input: ..., expected: ..., description: ...}]';