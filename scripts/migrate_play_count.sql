-- Migration: profiles tablosuna play_count kolonu
-- 2026-07-04
-- Frontend her setCode çağrısında /api/v2/users/me/play-count endpoint'ini çağırır.

ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS play_count BIGINT DEFAULT 0 NOT NULL;

CREATE INDEX IF NOT EXISTS idx_profiles_play_count ON public.profiles(play_count DESC);

-- 📌 Retention policy (KVKK md. 5/e, md. 7):
--   Son etkileşimden 1 yıl sonra otomatik sıfırlanır.
--   Supabase scheduled function ile cron job olarak çalıştırılabilir:
--     UPDATE profiles SET play_count = 0
--     WHERE updated_at < NOW() - INTERVAL '1 year';
COMMENT ON COLUMN public.profiles.play_count IS
  'Toplam kod çalıştırma sayacı. 1 yıl inaktiflik sonrası sıfırlanır (KVKK retention).';