-- 2026-07-15: interview_attempts.language kolonu ekle
-- Hangi dilde denendi (python/javascript/rust) — istatistik + filtreleme
ALTER TABLE interview_attempts
  ADD COLUMN IF NOT EXISTS language VARCHAR(20) DEFAULT 'python';

-- Mevcut kayitlar icin default 'python' (zaten default, ama guvenlik icin)
UPDATE interview_attempts
SET language = 'python'
WHERE language IS NULL;

-- Index (filtreleme performansi icin)
CREATE INDEX IF NOT EXISTS idx_interview_attempts_language
  ON interview_attempts(language);

CREATE INDEX IF NOT EXISTS idx_interview_attempts_user_lang
  ON interview_attempts(user_id, language);
