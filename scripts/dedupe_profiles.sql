-- scripts/dedupe_profiles.sql
--
-- 2026-07-19: Profile tablosundaki duplicate satırları temizle.
-- Supabase Dashboard → SQL Editor → New query → yapıştır → Run
--
-- Bu sorgu 4 adimda duplicate'leri temizler:
--   1) Email ile duplicate
--   2) Username ile duplicate
--   3) NULL email/username
--   4) UNIQUE constraint ekle (ileride duplicate olmasin)
--
-- Her adimi AYRI AYRI calistir. Adim 1 sonucu bossa (0 row) duplicate yok
-- demektir, sonraki adimlara gecmeye gerek yok.

-- ════════════════════════════════════════════════════════════════
-- ADIM 1: Email duplicate kontrol + temizleme
-- ════════════════════════════════════════════════════════════════

-- 1a) Mevcut durum (kac duplicate var?)
SELECT email, COUNT(*) as adet, array_agg(id::text ORDER BY created_at) as ids
FROM public.profiles
WHERE email IS NOT NULL
GROUP BY email
HAVING COUNT(*) > 1
ORDER BY adet DESC;

-- 1b) Duplicate'leri sil — en eski satiri tut, yenileri sil
--     ON DELETE CASCADE: interview_attempts FK'si otomatik silinir
DELETE FROM public.profiles p
WHERE p.id IN (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (
      PARTITION BY email
      ORDER BY created_at ASC
    ) as rn
    FROM public.profiles
    WHERE email IS NOT NULL
  ) ranked
  WHERE rn > 1
);

-- ════════════════════════════════════════════════════════════════
-- ADIM 2: Username duplicate temizleme (sadece varsa)
-- ════════════════════════════════════════════════════════════════

-- 2a) Username duplicate kontrol
SELECT username, COUNT(*) as adet
FROM public.profiles
WHERE username IS NOT NULL
GROUP BY username
HAVING COUNT(*) > 1
ORDER BY adet DESC;

-- 2b) Username'i unique yapmak icin, yeni olana "-{id_prefix}" ekle
--     Boylece eski username korunur, yenisi farkli olur
UPDATE public.profiles
SET username = username || '-' || SUBSTRING(id::text, 1, 8)
WHERE id IN (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (
      PARTITION BY username
      ORDER BY created_at ASC
    ) as rn
    FROM public.profiles
    WHERE username IS NOT NULL
  ) ranked
  WHERE rn > 1
);

-- ════════════════════════════════════════════════════════════════
-- ADIM 3: NULL email/username olan user'lari doldur
-- ════════════════════════════════════════════════════════════════

-- 3a) email NULL olan profillere auth.users'tan email fallback
UPDATE public.profiles p
SET email = au.email
FROM auth.users au
WHERE p.id = au.id
  AND p.email IS NULL
  AND au.email IS NOT NULL;

-- 3b) username NULL olan profillere email'den turetilmis username ver
UPDATE public.profiles
SET username = split_part(email, '@', 1)
WHERE username IS NULL
  AND email IS NOT NULL;

-- ════════════════════════════════════════════════════════════════
-- ADIM 4: UNIQUE constraint ekle (ileride duplicate olmasin)
-- ════════════════════════════════════════════════════════════════

-- email UNIQUE (NULL'lara izin verir — birden fazla NULL olabilir)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'profiles_email_unique'
  ) THEN
    ALTER TABLE public.profiles
      ADD CONSTRAINT profiles_email_unique UNIQUE (email);
  END IF;
END $$;

-- username UNIQUE
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'profiles_username_unique'
  ) THEN
    ALTER TABLE public.profiles
      ADD CONSTRAINT profiles_username_unique UNIQUE (username);
  END IF;
END $$;

-- ════════════════════════════════════════════════════════════════
-- SONUC: Temizlik sonrasi durum
-- ════════════════════════════════════════════════════════════════

SELECT
  COUNT(*) as toplam_profil,
  COUNT(DISTINCT email) as unique_email,
  COUNT(DISTINCT username) as unique_username,
  COUNT(CASE WHEN email IS NULL THEN 1 END) as null_email,
  COUNT(CASE WHEN username IS NULL THEN 1 END) as null_username
FROM public.profiles;
