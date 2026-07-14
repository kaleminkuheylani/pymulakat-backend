-- scripts/ai_usage_rls_update.sql
-- ai_usage RLS policy güncellemesi (v3 — UPDATE + INSERT için)
--
-- 2026-07-14: Mevcut policy sadece SELECT. service_role ve user için
--   INSERT/UPDATE/DELETE policy'leri eksik. Backend increment endpoint'i
--   service_role_key ile INSERT/UPDATE yapar, RLS engellerse
--   DB'ye yazamaz, sayfa yenileyince 0/10 doner.
--
-- Supabase Dashboard > SQL Editor > Yapıştır > Çalıştır

-- ═══════════════════════════════════════════════════════════════
-- 1) Mevcut policy'leri temizle
-- ═══════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "Users can read own ai usage" ON ai_usage;
DROP POLICY IF EXISTS "Service role can manage ai_usage" ON ai_usage;
DROP POLICY IF EXISTS "Users can insert own ai_usage" ON ai_usage;
DROP POLICY IF EXISTS "Users can update own ai_usage" ON ai_usage;
DROP POLICY IF EXISTS "Users can delete own ai_usage" ON ai_usage;

-- ═══════════════════════════════════════════════════════════════
-- 2) service_role: TÜM işlemler (SELECT, INSERT, UPDATE, DELETE)
-- ═══════════════════════════════════════════════════════════════
-- Backend service_role_key ile ai_usage tablosuna yazar.
-- Service_role normalde RLS bypass eder, ama bazı Supabase
-- konfigürasyonlarında policy'ye tabi olabilir (RLS force).
-- Explicit policy ile garantili.
CREATE POLICY "Service role full access ai_usage" ON ai_usage
  FOR ALL TO service_role
  USING (true)
  WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════
-- 3) authenticated user: kendi satırını SELECT edebilir
-- ═══════════════════════════════════════════════════════════════
-- Frontend (kullanıcı authenticated) kendi ai_usage satırını
-- okuyabilir (debug, görüntüleme). INSERT/UPDATE backend yapar.
CREATE POLICY "Users read own ai_usage" ON ai_usage
  FOR SELECT TO authenticated
  USING (auth.uid() = user_id);

-- ═══════════════════════════════════════════════════════════════
-- 4) anon user: hiçbir şey yapamaz
-- ═══════════════════════════════════════════════════════════════
-- Misafir user AI feedback kullanamaz (limit 0). RLS deny.

-- ═══════════════════════════════════════════════════════════════
-- 5) Realtime subscription policy (opsiyonel)
-- ═══════════════════════════════════════════════════════════════
-- pg_dump, replication vb. için gerekebilir.

-- ═══════════════════════════════════════════════════════════════
-- 6) Test
-- ═══════════════════════════════════════════════════════════════
-- Service role ile INSERT test (Supabase Dashboard SQL Editor):
-- INSERT INTO ai_usage (user_id, period_start, used_count)
--   VALUES ((SELECT id FROM profiles LIMIT 1), '2026-07-14', 1)
--   RETURNING *;
--
-- Başarılıysa RLS OK. Hata 'permission denied for table ai_usage'
-- ise service_role_key Supabase'da RLS bypass etmiyor demektir
-- (nadir). Bu durumda service_role policy'si gerekli.
