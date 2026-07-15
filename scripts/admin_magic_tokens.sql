-- 2026-07-15: admin_magic_tokens — admin magic link auth
-- Email-only login: Resend ile link gonder, kullanici tiklayinca session ac
CREATE TABLE IF NOT EXISTS admin_magic_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_email TEXT NOT NULL,
  token_hash TEXT NOT NULL UNIQUE,    -- SHA256(token + SECRET)
  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ,                -- tek kullanimlik
  ip TEXT,
  user_agent TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_admin_magic_tokens_hash
  ON admin_magic_tokens(token_hash);

CREATE INDEX IF NOT EXISTS idx_admin_magic_tokens_email
  ON admin_magic_tokens(user_email, created_at DESC);

-- RLS: service_role full access
ALTER TABLE admin_magic_tokens ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "admin_magic_tokens service_role full" ON admin_magic_tokens;
CREATE POLICY "admin_magic_tokens service_role full"
  ON admin_magic_tokens FOR ALL TO service_role
  USING (true) WITH CHECK (true);
