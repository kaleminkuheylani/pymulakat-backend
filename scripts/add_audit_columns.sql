-- scripts/add_audit_columns.sql
-- questions tablosuna denetim kolonları ekle.
--
-- ⚠️ MEMORY KURALI (2026-07-11):
--  - questions tablosuna sütun ekleme YASAK (column freeze)
--  - Bu script kullanıcı direktifi ile (2026-07-12 denetim özelliği)
--  - İstisna: denetim state'i tutmak için 3 kolon gerekli
--  - ASLA Railway üzerinden çalıştır, sadece Supabase SQL Editor
--
-- 📋 Idempotent. Birden fazla çalıştırılabilir.

BEGIN;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 1) is_audited: denetim geçti mi?                                  ║
-- ╚═══════════════════════════════════════════════════════════════════╝

ALTER TABLE public.questions
    ADD COLUMN IF NOT EXISTS is_audited BOOLEAN DEFAULT FALSE;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 2) audited_at: son denetim zamanı                                 ║
-- ╚═══════════════════════════════════════════════════════════════════╝

ALTER TABLE public.questions
    ADD COLUMN IF NOT EXISTS audited_at TIMESTAMPTZ;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 3) audit_status: passed/failed/pending                            ║
-- ╚═══════════════════════════════════════════════════════════════════╝

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'questions' AND column_name = 'audit_status'
    ) THEN
        ALTER TABLE public.questions
            ADD COLUMN audit_status TEXT DEFAULT 'pending'
            CHECK (audit_status IN ('pending', 'passed', 'failed'));
    END IF;
END $$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 4) Index: denetlenmemiş sorular hızlı bulunsun                   ║
-- ╚═══════════════════════════════════════════════════════════════════╝

CREATE INDEX IF NOT EXISTS idx_questions_audit_status
    ON public.questions (audit_status)
    WHERE audit_status = 'pending';

CREATE INDEX IF NOT EXISTS idx_questions_is_audited
    ON public.questions (is_audited)
    WHERE is_audited = FALSE;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 5) Mevcut soruları pending olarak işaretle                       ║
-- ╚═══════════════════════════════════════════════════════════════════╝

UPDATE public.questions
SET audit_status = 'pending'
WHERE audit_status IS NULL;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 6) Schema reload (PostgREST)                                      ║
-- ╚═══════════════════════════════════════════════════════════════════╝

NOTIFY pgrst, 'reload schema';

COMMIT;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ DOĞRULAMA                                                          ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- SELECT column_name, data_type, is_nullable, column_default
--   FROM information_schema.columns
--  WHERE table_name = 'questions'
--    AND column_name IN ('is_audited', 'audited_at', 'audit_status');

-- Audit durumu özeti
-- SELECT
--   audit_status,
--   COUNT(*) as count
-- FROM public.questions
-- GROUP BY audit_status;

-- ⚠️ ROLLBACK:
-- DROP INDEX IF EXISTS idx_questions_audit_status;
-- DROP INDEX IF EXISTS idx_questions_is_audited;
-- ALTER TABLE public.questions
--   DROP CONSTRAINT IF EXISTS questions_audit_status_check;
-- ALTER TABLE public.questions
--   DROP COLUMN IF EXISTS audit_status,
--   DROP COLUMN IF EXISTS audited_at,
--   DROP COLUMN IF EXISTS is_audited;
