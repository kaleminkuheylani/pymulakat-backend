-- pymulakat-backend: onboarding anket tablosu
-- 2026-07-18: Kullanici memnuniyet anketi
-- 3 soru: kaynak, degerlendirme, yas araligi
-- dismissed = true ise bir daha gosterme
--
-- Calistir: Supabase SQL Editor
--
-- ===========================================
-- ADIM 1 — Tablo
-- ===========================================
CREATE TABLE IF NOT EXISTS survey_responses (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Q1: Bizi nereden buldunuz?
  -- google | reddit | youtube | x_twitter | linkedin | friend | other | skip
  source VARCHAR(32),

  -- Q2: Nasil buldunuz?
  -- great | good | meh | questions_weak | platform_useless | learning_insufficient | skip
  rating VARCHAR(32),

  -- Q3: Yas araligi
  -- 15_18 | 18_25 | 25_35 | 35_plus | skip
  age_range VARCHAR(16),

  -- Opsiyonel aciklama
  feedback_text TEXT,

  -- Bir daha gosterme (kullanici 'Atla' veya 'Gonder' basarsa)
  dismissed BOOLEAN NOT NULL DEFAULT FALSE,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ===========================================
-- ADIM 2 — Indexler
-- ===========================================
-- Kullanici basina tek anket (UNIQUE)
CREATE UNIQUE INDEX IF NOT EXISTS idx_survey_user
  ON survey_responses (user_id);

-- Hızlı sorgu: dismissed = false olanlar
CREATE INDEX IF NOT EXISTS idx_survey_dismissed
  ON survey_responses (dismissed) WHERE dismissed = FALSE;

-- ===========================================
-- ADIM 3 — RLS (Row Level Security)
-- ===========================================
ALTER TABLE survey_responses ENABLE ROW LEVEL SECURITY;

-- Kullanici kendi anketini gorebilir
DROP POLICY IF EXISTS "Users can view own survey" ON survey_responses;
CREATE POLICY "Users can view own survey"
  ON survey_responses FOR SELECT
  USING (auth.uid() = user_id);

-- Kullanici kendi anketini ekleyebilir/guncelleyebilir
DROP POLICY IF EXISTS "Users can insert own survey" ON survey_responses;
CREATE POLICY "Users can insert own survey"
  ON survey_responses FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own survey" ON survey_responses;
CREATE POLICY "Users can update own survey"
  ON survey_responses FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Backend service role icin (FastAPI)
-- Not: Supabase service_role key RLS bypass eder, ek policy gerekmez

-- ===========================================
-- ADIM 4 — updated_at trigger
-- ===========================================
CREATE OR REPLACE FUNCTION update_survey_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS survey_updated_at ON survey_responses;
CREATE TRIGGER survey_updated_at
  BEFORE UPDATE ON survey_responses
  FOR EACH ROW
  EXECUTE FUNCTION update_survey_updated_at();

-- ===========================================
-- ADIM 5 — Dogrulama
-- ===========================================
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'survey_responses'
ORDER BY ordinal_position;
