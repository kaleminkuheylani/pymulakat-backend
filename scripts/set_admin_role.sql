-- scripts/set_admin_role.sql
-- Kaleminkuheylani hesabini Supabase admin yap.
-- KVKK: sadece uye'nin kendi hesabi. app_metadata.role = 'admin'.
-- 
-- KULLANIM: Supabase Dashboard → SQL Editor → yapistir calistir
-- VEYA: psql -h <host> -U postgres -d postgres -f scripts/set_admin_role.sql

-- 1) Kaleminkuheylani hesabini admin yap
UPDATE auth.users
SET app_metadata = app_metadata || '{"role": "admin", "provider": "email"}'::jsonb
WHERE email = 'kaleminkuheylani@gmail.com'
  AND (app_metadata->>'role') IS DISTINCT FROM 'admin';

-- 2) Dogrulama
SELECT 
  id,
  email,
  app_metadata->>'role' AS admin_role,
  created_at
FROM auth.users
WHERE email = 'kaleminkuheylani@gmail.com';

-- 3) Tum admin'leri listele (gerektiginde)
-- SELECT id, email, app_metadata->>'role' FROM auth.users 
-- WHERE app_metadata->>'role' = 'admin';
