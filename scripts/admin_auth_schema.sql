-- scripts/admin_auth_schema.sql
-- Admin auth: mfa_secret, failed_login_count, lockout, audit_log
--
-- Supabase Dashboard > SQL Editor > Yapistir Calistir

-- ═══════════════════════════════════════════════════════════════
-- 1) admin_mfa tablosu (user_id → TOTP secret)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS admin_mfa (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  secret TEXT NOT NULL,            -- TOTP secret (base32)
  enabled BOOLEAN NOT NULL DEFAULT FALSE,
  backup_codes TEXT[] DEFAULT ARRAY[]::TEXT[],
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  enabled_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_admin_mfa_enabled ON admin_mfa(enabled);

-- ═══════════════════════════════════════════════════════════════
-- 2) admin_sessions (HttpOnly cookie session tracking)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS admin_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  ip INET,
  user_agent TEXT,
  issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  revoked BOOLEAN NOT NULL DEFAULT FALSE,
  revoked_at TIMESTAMPTZ,
  revoke_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_admin_sessions_user ON admin_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires ON admin_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_revoked ON admin_sessions(revoked) WHERE revoked = FALSE;

-- ═══════════════════════════════════════════════════════════════
-- 3) admin_audit_log (her login attempt + admin action)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS admin_audit_log (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  user_email TEXT,
  action TEXT NOT NULL,            -- 'login' | 'login_failed' | 'mfa_verify' | 'logout' | 'admin_action' | 'guard_deny'
  ip INET,
  user_agent TEXT,
  success BOOLEAN NOT NULL,
  detail JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_user ON admin_audit_log(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_audit_action ON admin_audit_log(action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_audit_failed ON admin_audit_log(success, created_at DESC) WHERE success = FALSE;

-- ═══════════════════════════════════════════════════════════════
-- 4) admin_lockout (5 basarisiz login → 15dk lockout)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS admin_lockout (
  user_email TEXT PRIMARY KEY,
  failed_count INT NOT NULL DEFAULT 0,
  last_attempt_at TIMESTAMPTZ,
  locked_until TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_admin_lockout_until ON admin_lockout(locked_until);

-- ═══════════════════════════════════════════════════════════════
-- 5) Admin password storage (Supabase auth.users encrypted_password
--    zaten Supabase tarafinda. bcrypt AYRICA olusturmaya gerek yok.
--    Sadece MFA + session + audit eklenir.
-- ═══════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════
-- 6) İlk admin için MFA setup (örnek: kaleminkuheylani@gmail.com)
-- ═══════════════════════════════════════════════════════════════
-- INSERT INTO admin_mfa (user_id, secret, enabled)
-- SELECT id, 'JBSWY3DPEHPK3PXP', FALSE  -- placeholder, /admin/auth/setup-mfa ile degistirilir
-- FROM auth.users WHERE email = 'kaleminkuheylani@gmail.com';
-- 
-- Bu satır YAPISTIRMA — kullanıcı login olduktan sonra
-- /api/v2/admin/auth/setup-mfa endpoint'i TOTP secret + QR uretir.

-- ═══════════════════════════════════════════════════════════════
-- RLS: admin tablolari service_role'dan okunur (RLS bypass)
-- ═══════════════════════════════════════════════════════════════
ALTER TABLE admin_mfa ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_lockout ENABLE ROW LEVEL SECURITY;

-- Policy: sadece service_role erisebilir (RLS bypass zaten service_key ile olur)
DROP POLICY IF EXISTS "service_role_all_admin_mfa" ON admin_mfa;
CREATE POLICY "service_role_all_admin_mfa" ON admin_mfa
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);

DROP POLICY IF EXISTS "service_role_all_admin_sessions" ON admin_sessions;
CREATE POLICY "service_role_all_admin_sessions" ON admin_sessions
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);

DROP POLICY IF EXISTS "service_role_all_admin_audit_log" ON admin_audit_log;
CREATE POLICY "service_role_all_admin_audit_log" ON admin_audit_log
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);

DROP POLICY IF EXISTS "service_role_all_admin_lockout" ON admin_lockout;
CREATE POLICY "service_role_all_admin_lockout" ON admin_lockout
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);
