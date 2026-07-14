-- scripts/ai_feedback_profile.sql
-- AI Feedback quota — profiles tablosuna entegre (tek kaynak).
--
-- 2026-07-14: ayrı ai_feedback_usage tablosu gereksiz, profiles'a 2
--   column ekle. Misafir user AI kullanamadığı için (MAX_FREE_FEEDBACK_ANON=0)
--   anon_user_id tracking'e gerek yok. Sadece auth user için quota.
--
-- Supabase Dashboard > SQL Editor > Yapıştır > Çalıştır

-- ═══════════════════════════════════════════════════════════════
-- 1) profiles tablosuna AI feedback column'ları
-- ═══════════════════════════════════════════════════════════════
ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS ai_feedback_used INT NOT NULL DEFAULT 0;

ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS ai_feedback_period_start DATE;

-- Index: auth user_id ile hızlı lookup
CREATE INDEX IF NOT EXISTS idx_profiles_user_id
  ON profiles(user_id)
  WHERE user_id IS NOT NULL;

-- Unique: bir auth user'ın bir profile satırı olsun
CREATE UNIQUE INDEX IF NOT EXISTS uniq_profiles_user_id
  ON profiles(user_id)
  WHERE user_id IS NOT NULL;

-- ═══════════════════════════════════════════════════════════════
-- 2) Eski ai_feedback_usage tablosunu kaldır (gereksiz)
-- ═══════════════════════════════════════════════════════════════
DROP TABLE IF EXISTS ai_feedback_usage CASCADE;

-- Helper function'lar da kaldır (artık gerek yok)
DROP FUNCTION IF EXISTS get_or_create_ai_feedback_usage(UUID, UUID, DATE);
DROP FUNCTION IF EXISTS increment_ai_feedback_usage(UUID, UUID, DATE, INT);
