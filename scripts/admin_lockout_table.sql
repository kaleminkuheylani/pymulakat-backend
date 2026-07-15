-- 2026-07-15: admin_lockout tablosu (admin auth icin)
-- Lockout tracking: 5 fail → 15dk lockout
CREATE TABLE IF NOT EXISTS admin_lockout (
  user_email TEXT PRIMARY KEY,
  failed_count INT NOT NULL DEFAULT 0,
  last_attempt_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  locked_until TIMESTAMPTZ
);

-- Index: lockout sorgusu (WHERE locked_until > now())
CREATE INDEX IF NOT EXISTS idx_admin_lockout_locked_until
  ON admin_lockout(locked_until)
  WHERE locked_until IS NOT NULL;

-- RLS: service_role full access (admin_auth.py SUPABASE_SERVICE_ROLE_KEY kullaniyor)
ALTER TABLE admin_lockout ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "admin_lockout service_role full" ON admin_lockout;
CREATE POLICY "admin_lockout service_role full"
  ON admin_lockout
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);
