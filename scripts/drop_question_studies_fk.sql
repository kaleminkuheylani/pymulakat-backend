-- scripts/drop_question_studies_fk.sql
-- question_studies FK constraint'ini kaldır — CSV-first mimari.
--
-- Neden: Production DB'de 'questions' tablosu boş (CSV source of truth).
-- Question satırı yoksa FK hatası yüzünden study seed yapılamıyor.
-- FK kaldırılınca:
--   - 30 study satırı eklenebilir
--   - question_id sadece 'integer kimlik', referans değil
--   - 'related_question_ids' için foreign data wrapper'a gerek yok
--
-- Veri bütünlüğü korunur:
--   - UNIQUE INDEX (question_id) — aynı soruya 2 study engellenir
--   - study_slug UNIQUE — URL çakışması engellenir
--
-- Migration IDEMPOTENT: zaten drop edilmişse hata vermez.

BEGIN;

-- 1) Mevcut FK constraint'i bul ve düşür
DO $$
DECLARE
    fk_name text;
BEGIN
    SELECT conname INTO fk_name
    FROM pg_constraint
    WHERE conrelid = 'public.question_studies'::regclass
      AND contype = 'f'
      AND pg_get_constraintdef(oid) LIKE '%REFERENCES%questions%';

    IF fk_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE public.question_studies DROP CONSTRAINT %I', fk_name);
        RAISE NOTICE 'FK dropped: %', fk_name;
    ELSE
        RAISE NOTICE 'FK bulunamadı (zaten kaldırılmış?)';
    END IF;
END $$;

-- 2) UNIQUE INDEX ekle — FK yerine veri bütünlüğü için
CREATE UNIQUE INDEX IF NOT EXISTS idx_question_studies_question_id_unique
    ON public.question_studies (question_id);

-- 3) Schema reload for PostgREST
NOTIFY pgrst, 'reload schema';

COMMIT;

-- Kontrol: kalan constraint'ler
SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'public.question_studies'::regclass
ORDER BY conname;
