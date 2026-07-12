-- scripts/page_views_schema.sql
-- Page views tracking tablosu.
--
-- Supabase Dashboard > SQL Editor > Yapistir Calistir

CREATE TABLE IF NOT EXISTS page_views (
  id BIGSERIAL PRIMARY KEY,
  path TEXT NOT NULL,             -- /temelleri/palindrome-checker
  category TEXT,                  -- temelleri (opsiyonel)
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,  -- null = anonim
  ip INET,                       -- KVKK: anonymize edilebilir
  user_agent TEXT,
  referrer TEXT,                 -- nereden geldi
  session_id TEXT,               -- browser session (cookie'siz fingerprint)
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_page_views_path ON page_views(path, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_page_views_category ON page_views(category, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_page_views_user ON page_views(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_page_views_created ON page_views(created_at DESC);

-- DAILY AGGREGATE (performans: 85M raw row yerine 1M aggregate)
CREATE TABLE IF NOT EXISTS page_views_daily (
  path TEXT NOT NULL,
  category TEXT,
  view_date DATE NOT NULL,
  view_count INT NOT NULL DEFAULT 0,
  unique_sessions INT NOT NULL DEFAULT 0,
  PRIMARY KEY (path, view_date)
);

CREATE INDEX IF NOT EXISTS idx_pvd_date ON page_views_daily(view_date DESC);
CREATE INDEX IF NOT EXISTS idx_pvd_category_date ON page_views_daily(category, view_date DESC);

-- RLS: service_role full access (backend admin endpoint'leri)
ALTER TABLE page_views ENABLE ROW LEVEL SECURITY;
ALTER TABLE page_views_daily ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_all_pv" ON page_views;
CREATE POLICY "service_role_all_pv" ON page_views
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);

DROP POLICY IF EXISTS "service_role_all_pvd" ON page_views_daily;
CREATE POLICY "service_role_all_pvd" ON page_views_daily
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);

-- ═══════════════════════════════════════════════════════════════
-- RPC: increment_page_view_daily (atomic counter++)
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION increment_page_view_daily(
  p_path TEXT,
  p_category TEXT,
  p_date DATE
)
RETURNS void AS $$
BEGIN
  INSERT INTO page_views_daily (path, category, view_date, view_count, unique_sessions)
  VALUES (p_path, p_category, p_date, 1, 1)
  ON CONFLICT (path, view_date)
  DO UPDATE SET view_count = page_views_daily.view_count + 1;
END;
$$ LANGUAGE plpgsql;
