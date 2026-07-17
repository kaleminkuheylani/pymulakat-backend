-- 2026-07-17: question_reports tablosu
-- Kullanici "Soru hataliysa lutfen bildir" butonuna basarak screenshot + aciklama gonderir
-- Sadece authenticated user (anonim: 0 hak)
-- Supabase SQL Editor'de calistir veya backend startup'ta auto-migration

CREATE TABLE IF NOT EXISTS question_reports (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  question_id INTEGER NOT NULL,
  question_slug TEXT,
  category TEXT,
  screenshot_base64 TEXT,         -- base64 inline (kucuk dosyalar, <2MB)
  description TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'reviewing', 'closed', 'spam')),
  admin_note TEXT,                 -- admin geri bildirim (ileride)
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index: user bazli sorgular (kullanicinin kendi raporlari)
CREATE INDEX IF NOT EXISTS idx_question_reports_user 
  ON question_reports(user_id, created_at DESC);

-- Index: status bazli (admin paneli / open reports)
CREATE INDEX IF NOT EXISTS idx_question_reports_status 
  ON question_reports(status, created_at DESC) 
  WHERE status IN ('open', 'reviewing');

-- Index: question bazli (hangi soruda en cok rapor var)
CREATE INDEX IF NOT EXISTS idx_question_reports_question 
  ON question_reports(question_id, created_at DESC);

-- RLS: user sadece kendi raporlarini okuyabilir, insert edebilir
ALTER TABLE question_reports ENABLE ROW LEVEL SECURITY;

-- Kullanici kendi raporlarini gorebilir
DROP POLICY IF EXISTS "Users can view their own reports" ON question_reports;
CREATE POLICY "Users can view their own reports" 
  ON question_reports FOR SELECT 
  USING (auth.uid() = user_id);

-- Kullanici yeni rapor ekleyebilir
DROP POLICY IF EXISTS "Users can insert their own reports" ON question_reports;
CREATE POLICY "Users can insert their own reports" 
  ON question_reports FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

-- Service role tum tablolara erisebilir (admin islemleri)
-- (RLS service_role icin default bypass)

-- Trigger: updated_at auto-update
CREATE OR REPLACE FUNCTION update_question_reports_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_question_reports_updated_at ON question_reports;
CREATE TRIGGER trg_question_reports_updated_at
  BEFORE UPDATE ON question_reports
  FOR EACH ROW
  EXECUTE FUNCTION update_question_reports_updated_at();
