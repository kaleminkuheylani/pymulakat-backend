-- scripts/ai_usage_table.sql
-- AI Feedback quota — ayrı tablo (profiles'dan izole).
--
-- 2026-07-14: profiles tablosundan ai_feedback_used + period_start
--   kaldırıldı, ayrı ai_usage tablosu oluşturuldu. Neden:
--   - Separation of concerns: auth/profil vs. quota farklı tablolar
--   - RLS policies kolay (user_id bazlı)
--   - profiles tablosu şişmez (her feature için column eklemek yerine
--     ilgili tablo)
--   - Backend service_role_key ile yazar (RLS bypass), user kendi
--     satırını okuyabilir
--   - Index: (user_id, period_start) unique — günlük reset atomik
--
-- Supabase Dashboard > SQL Editor > Yapıştır > Çalıştır

-- ═══════════════════════════════════════════════════════════════
-- 1) ai_usage tablosu
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS ai_usage (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  used_count INT NOT NULL DEFAULT 0,
  period_start DATE NOT NULL,                    -- Gün başı (YYYY-MM-DD)
  last_used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Bir user günde tek satır (atomik günlük quota)
  CONSTRAINT uniq_ai_usage_user_period UNIQUE (user_id, period_start)
);

-- Index: Auth user için hızlı lookup
CREATE INDEX IF NOT EXISTS idx_ai_usage_user_period
  ON ai_usage(user_id, period_start);

-- ═══════════════════════════════════════════════════════════════
-- 2) RLS (Row Level Security) — user sadece kendi satırını görsün
-- ═══════════════════════════════════════════════════════════════
ALTER TABLE ai_usage ENABLE ROW LEVEL SECURITY;

-- Kullanıcı kendi satırını okuyabilir
CREATE POLICY "Users can read own ai usage"
  ON ai_usage FOR SELECT
  USING (auth.uid() = user_id);

-- Backend service_role_key ile yazar (RLS bypass)
-- INSERT/UPDATE/DELETE policy service_role'a açık değil çünkü
-- service_role zaten RLS bypass eder. Sadece backend bu tabloya
-- yazar (Next.js proxy üzerinden).

-- ═══════════════════════════════════════════════════════════════
-- 3) Eski profiles.ai_feedback_used + period_start kaldır
-- ═══════════════════════════════════════════════════════════════
ALTER TABLE profiles
  DROP COLUMN IF EXISTS ai_feedback_used;

ALTER TABLE profiles
  DROP COLUMN IF EXISTS ai_feedback_period_start;

-- (Önceki migration'da eklenen user_id FK Supabase auth'a bağlıydı,
--  şimdi user_id profiles.id'ye FK. Bu daha doğru — pymulakat'in
--  kendi UUID sistemiyle uyumlu.)
