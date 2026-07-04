-- Migration: interview_attempts tablosu
-- 2026-07-04
-- Her başarılı/başarısız kod çalıştırmasını kaydeder.
-- user_code KAYDEDILMIYOR (KVKK uyumu, kod client-side Pyodide'da çalışıyor).

CREATE TABLE IF NOT EXISTS public.interview_attempts (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  question_id BIGINT NOT NULL,
  passed_tests INTEGER NOT NULL DEFAULT 0,
  total_tests INTEGER NOT NULL DEFAULT 0,
  success BOOLEAN NOT NULL DEFAULT FALSE,
  execution_time_ms INTEGER NOT NULL DEFAULT 0,
  hints_used INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- İndeksler (raporlama + feed için)
CREATE INDEX IF NOT EXISTS idx_attempts_user_created
  ON public.interview_attempts(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_attempts_question
  ON public.interview_attempts(question_id);

CREATE INDEX IF NOT EXISTS idx_attempts_success
  ON public.interview_attempts(success, created_at DESC);

-- RLS
ALTER TABLE public.interview_attempts ENABLE ROW LEVEL SECURITY;

-- Kullanıcı kendi attemptlerini okuyabilir
DROP POLICY IF EXISTS "Users can read own attempts" ON public.interview_attempts;
CREATE POLICY "Users can read own attempts"
  ON public.interview_attempts
  FOR SELECT
  USING (auth.uid() = user_id);

-- INSERT service_role üzerinden yapılıyor (RLS bypass)
-- Bu yüzden INSERT policy gerekmiyor.
-- (Yine de auth.uid() ile kendi yazabilsin istenirse:)
DROP POLICY IF EXISTS "Users can insert own attempts" ON public.interview_attempts;
CREATE POLICY "Users can insert own attempts"
  ON public.interview_attempts
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Comment
COMMENT ON TABLE public.interview_attempts IS
  'Kod çalıştırma attemptleri. user_code KAYDEDILMIYOR (KVKK).';
COMMENT ON COLUMN public.interview_attempts.user_code IS
  'DEPRECATED: Hiçbir zaman yazma. Kod Pyodide WASM ile client-side çalışıyor.';