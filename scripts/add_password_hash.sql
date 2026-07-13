-- Supabase SQL Editor → calistir
-- Mevcut profiles tablosuna password_hash kolonu ekle
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS password_hash TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS display_name TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS failed_count INT NOT NULL DEFAULT 0;

-- Index
CREATE INDEX IF NOT EXISTS idx_profiles_admin ON profiles(is_admin) WHERE is_admin = TRUE;

-- kaleminkuheylani@gmail.com'a password_hash yok, login calismasi icin:
-- (hash'i Python ile olusturup SQL'de set etmek lazim)
-- Veya backend login endpoint'i password_hash NULL ise sifre kabul etsin
-- (güvenli degil ama hizli test icin)
