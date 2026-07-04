-- Migration: profiles tablosuna play_count kolonu
-- 2026-07-04
-- Frontend her setCode çağrısında /api/v2/users/me/play-count endpoint'ini çağırır.

ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS play_count BIGINT DEFAULT 0 NOT NULL;

CREATE INDEX IF NOT EXISTS idx_profiles_play_count ON public.profiles(play_count DESC);