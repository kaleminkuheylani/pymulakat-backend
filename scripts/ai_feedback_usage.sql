-- scripts/ai_feedback_usage.sql
-- AI Feedback quota tracking — per-user monthly limit
--
-- 2026-07-14: Production-ready quota system. localStorage istemcide
-- kolayca bypass edilebiliyordu. DB-side enforcement:
--   - user_id UUID FK (auth.users)
--   - used_count INT (bu ay kullanılan)
--   - period_start DATE (ay başlangıcı)
--   - Unique (user_id, period_start) — ay başına tek satır
--
-- 2026-07-14 v2: Misafir (anon) kullanıcılar için fallback. auth_user_id
--   NULL olabilir, anon_token (cookie/random) ile takip. Backend
--   anon_user_id alanına random UUID set eder (misafir başına 5 hak).
--
-- Supabase Dashboard > SQL Editor > Yapıştır > Çalıştır

-- ═══════════════════════════════════════════════════════════════
-- 1) ai_feedback_usage tablosu
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS ai_feedback_usage (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  anon_user_id UUID,                    -- Misafir (anon) için
  period_start DATE NOT NULL,            -- Ay başı (YYYY-MM-01)
  used_count INT NOT NULL DEFAULT 0,
  last_used_at TIMESTAMPTZ,
  created_at TIMISTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Auth user veya anon user (en az biri olmalı)
  CONSTRAINT chk_user_or_anon CHECK (
    user_id IS NOT NULL OR anon_user_id IS NOT NULL
  )
);

-- Index: Auth user için hızlı lookup (en yaygın sorgu)
CREATE INDEX IF NOT EXISTS idx_ai_feedback_usage_user_period
  ON ai_feedback_usage(user_id, period_start)
  WHERE user_id IS NOT NULL;

-- Index: Anon user için
CREATE INDEX IF NOT EXISTS idx_ai_feedback_usage_anon_period
  ON ai_feedback_usage(anon_user_id, period_start)
  WHERE anon_user_id IS NOT NULL;

-- Aynı user/period için duplicate engelle
CREATE UNIQUE INDEX IF NOT EXISTS uniq_ai_feedback_usage_user_period
  ON ai_feedback_usage(user_id, period_start)
  WHERE user_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uniq_ai_feedback_usage_anon_period
  ON ai_feedback_usage(anon_user_id, period_start)
  WHERE anon_user_id IS NOT NULL;

-- ═══════════════════════════════════════════════════════════════
-- 2) RLS (Row Level Security) — user sadece kendi satırını görsün
-- ═══════════════════════════════════════════════════════════════
ALTER TABLE ai_feedback_usage ENABLE ROW LEVEL SECURITY;

-- Kullanıcı kendi satırını görebilir (anon hariç)
CREATE POLICY "Users can read own ai feedback usage"
  ON ai_feedback_usage FOR SELECT
  USING (auth.uid() = user_id);

-- Anon kullanıcılar için policy gerekmez (service role backend'den yazar)
-- Backend service_role_key ile INSERT/UPDATE yapar (RLS bypass)

-- ═══════════════════════════════════════════════════════════════
-- 3) Helper function: get_or_create_usage
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION get_or_create_ai_feedback_usage(
  p_user_id UUID,
  p_anon_user_id UUID,
  p_period_start DATE
)
RETURNS ai_feedback_usage
LANGUAGE plpgsql
SECURITY DEFINER  -- Function owner (postgres) olarak çalışsın
AS $$
DECLARE
  result ai_feedback_usage;
BEGIN
  -- Önce mevcut satırı bul
  IF p_user_id IS NOT NULL THEN
    SELECT * INTO result FROM ai_feedback_usage
      WHERE user_id = p_user_id AND period_start = p_period_start
      LIMIT 1;
  ELSIF p_anon_user_id IS NOT NULL THEN
    SELECT * INTO result FROM ai_feedback_usage
      WHERE anon_user_id = p_anon_user_id AND period_start = p_period_start
      LIMIT 1;
  END IF;

  -- Yoksa oluştur
  IF NOT FOUND THEN
    INSERT INTO ai_feedback_usage (user_id, anon_user_id, period_start, used_count)
      VALUES (p_user_id, p_anon_user_id, p_period_start, 0)
      RETURNING * INTO result;
  END IF;

  RETURN result;
END;
$$;

-- ═══════════════════════════════════════════════════════════════
-- 4) Helper function: increment_usage (atomik)
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION increment_ai_feedback_usage(
  p_user_id UUID,
  p_anon_user_id UUID,
  p_period_start DATE,
  p_max_count INT DEFAULT 10
)
RETURNS TABLE (
  used INT,
  limit_reached BOOLEAN,
  remaining INT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_used INT;
BEGIN
  -- Satırı al/oluştur
  PERFORM get_or_create_ai_feedback_usage(
    p_user_id, p_anon_user_id, p_period_start
  );

  -- Mevcut değeri oku
  IF p_user_id IS NOT NULL THEN
    SELECT used_count INTO v_used FROM ai_feedback_usage
      WHERE user_id = p_user_id AND period_start = p_period_start
      FOR UPDATE;
  ELSE
    SELECT used_count INTO v_used FROM ai_feedback_usage
      WHERE anon_user_id = p_anon_user_id AND period_start = p_period_start
      FOR UPDATE;
  END IF;

  -- Limit doluysa arttırma
  IF v_used >= p_max_count THEN
    RETURN QUERY SELECT v_used, TRUE, 0;
    RETURN;
  END IF;

  -- Artır
  IF p_user_id IS NOT NULL THEN
    UPDATE ai_feedback_usage
      SET used_count = used_count + 1,
          last_used_at = NOW(),
          updated_at = NOW()
      WHERE user_id = p_user_id AND period_start = p_period_start;
  ELSE
    UPDATE ai_feedback_usage
      SET used_count = used_count + 1,
          last_used_at = NOW(),
          updated_at = NOW()
      WHERE anon_user_id = p_anon_user_id AND period_start = p_period_start;
  END IF;

  v_used := v_used + 1;
  RETURN QUERY SELECT v_used, v_used >= p_max_count, GREATEST(0, p_max_count - v_used);
END;
$$;

-- ═══════════════════════════════════════════════════════════════
-- 5) Anonymous cleanup: 90 günden eski anon kayıtları sil
-- ═══════════════════════════════════════════════════════════════
-- Backend cron job veya Supabase scheduled function ile çağrılır.
-- Manuel: DELETE FROM ai_feedback_usage WHERE anon_user_id IS NOT NULL AND updated_at < NOW() - INTERVAL '90 days';
