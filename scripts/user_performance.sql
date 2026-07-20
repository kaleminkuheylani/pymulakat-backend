-- scripts/user_performance.sql
-- Kullanıcı toplam kullanım süresi + günlük streak tablosu.
-- 2026-07-20: user_performance tablosu oluşturuldu.

CREATE TABLE IF NOT EXISTS public.user_performance (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  total_usage_seconds INT NOT NULL DEFAULT 0,
  streak_count INT NOT NULL DEFAULT 0,
  last_active_date DATE,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_performance_user_id ON user_performance(user_id);

ALTER TABLE public.user_performance ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own performance" ON public.user_performance
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can upsert own performance" ON public.user_performance
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
