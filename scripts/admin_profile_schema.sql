-- scripts/admin_profile_schema.sql
-- Admin auth icin profiles tablosu.
-- auth.users + Supabase signIn bagimliligi yerine kendi tablomuz.

-- ═══════════════════════════════════════════════════════════════
-- 1) profiles tablosu (yoksa olustur)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  is_admin BOOLEAN NOT NULL DEFAULT FALSE,
  display_name TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_login_at TIMESTAMPTZ,
  failed_count INT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_admin ON profiles(is_admin) WHERE is_admin = TRUE;

-- ═══════════════════════════════════════════════════════════════
-- 2) RLS: sadece service_role okuyabilir
-- ═══════════════════════════════════════════════════════════════
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_all_profiles" ON profiles;
CREATE POLICY "service_role_all_profiles" ON profiles
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);

-- ═══════════════════════════════════════════════════════════════
-- 3) Seed: ilk admin user olustur
--    Email: kaleminkuheylani@gmail.com
--    Password: 515Ff?217589 (bcrypt hash)
-- ═══════════════════════════════════════════════════════════════
-- Hash'i Python ile olusturuyoruz (argon2 veya bcrypt)
-- Supabase SQL Editor'de sifre uretmek icin:
--   python3 -c "import bcrypt; print(bcrypt.hashpw(b'515Ff?217589', bcrypt.gensalt()).decode())"
-- Sonra UPDATE ile ekle.
-- Veya: setup-profile-admin endpoint'i ile backend'de otomatik kur.
