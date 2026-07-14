-- scripts/ai_usage_rls_fix.sql
-- ai_usage tablosu RLS policy fix (v2)
--
-- 2026-07-14: Mevcut policy sadece SELECT (user kendi satırını okur).
--   service_role INSERT/UPDATE yaparken RLS bypass etmeli, ama bazi
--   Supabase konfigurasyonlarinda service_role da policy'ye tabi.
--   Bu policy'ler ile backend (service_role_key) tüm işlemleri
--   yapabilir.
--
-- Supabase Dashboard > SQL Editor > Yapıştır > Çalıştır

-- ═══════════════════════════════════════════════════════════════
-- 1) service_role için tüm izinler (RLS bypass yerine explicit policy)
-- ═══════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "Service role can manage ai_usage" ON ai_usage;
CREATE POLICY "Service role can manage ai_usage" ON ai_usage
  FOR ALL TO service_role
  USING (true)
  WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════
-- 2) authenticated user sadece kendi satırını INSERT edebilir
-- ═══════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "Users can insert own ai_usage" ON ai_usage;
CREATE POLICY "Users can insert own ai_usage" ON ai_usage
  FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

-- ═══════════════════════════════════════════════════════════════
-- 3) Backend tüm işlemleri service_role_key ile yapar (pymulakat-backend)
-- ═══════════════════════════════════════════════════════════════
-- Bu noktada service_role policy FOR ALL (SELECT, INSERT, UPDATE, DELETE)
-- tum islemleri kapsar. Backend auth.get_user ile user_id alir, service_role
-- ile ai_usage INSERT/UPDATE yapar.
