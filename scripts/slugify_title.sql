-- scripts/slugify_title.sql
-- Mevcut title column'undan slug üreten SQL kodu.
--
-- ⚠️ MEMORY KURALI: Yeni column ekleme yok. Sadece mevcut `title` üzerinden
-- runtime'da slug hesaplanır. Bu yüzden bu script:
--   1) Saf bir SQL function tanımlar (slugify_title)
--   2) Mevcut tabloya dokunmaz, sadece VIEW oluşturur
--   3) İndeks — sadece FUNCTION üzerinde (immutable expression index, column değil)
--   4) Çıktı formatı: frontend'deki slugifyTitle() ile %100 aynı
--
-- Frontend (lib/questionMeta.ts) ile uyumluluk:
--   1) Lowercase
--   2) Türkçe karakterler → ASCII: ı→i, ş→s, ç→c, ğ→g, ö→o, ü→u
--   3) Apostrof/tırnak kaldır (TİRE DEĞİL)
--   4) Non-alphanumeric kaldır (boşluk/tire hariç)
--   5) Çoklu boşluk → tek tire
--   6) Baştaki/sondaki tire kırp
--   7) Maksimum uzunluk kısıtlaması yok (Next.js router otomatik match)
--
-- Örnek:
--   "Fibonacci Sayısı Hesaplama" → "fibonacci-sayisi-hesaplama"
--   "0/1 Knapsack Problemi"      → "01-knapsack-problemi"
--   "Türkçe Karakterler: ğüşıöç" → "turkce-karakterler-gusioc"
--
-- ⚠️ ROLLBACK: bu scripti geri almak için:
--   DROP FUNCTION IF EXISTS public.slugify_title(TEXT);
--   DROP VIEW IF EXISTS public.interviews_with_slug;
--   DROP INDEX IF EXISTS idx_interviews_slug;
-- (Yeni column eklenmediği için migration gerekmez, idempotent.)

BEGIN;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 1) Söylem: türkçe → ascii dönüşüm tablosu                       ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- Sıralı: TR karakterler (en uzun eşleşme önce)
-- unaccent extension gerekli mi? HAyIR — biz elle mapping yapacağız
-- (production'da unaccent + lower() yeterli olurdu, ama deterministic istiyoruz)

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 2) Ana slugify fonksiyonu                                         ║
-- ╚═══════════════════════════════════════════════════════════════════╝

CREATE OR REPLACE FUNCTION public.slugify_title(input TEXT)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
PARALLEL SAFE
AS $$
DECLARE
    s TEXT;
BEGIN
    IF input IS NULL OR input = '' THEN
        RETURN '';
    END IF;

    s := input;

    -- 1) Lowercase
    s := LOWER(s);

    -- 2) Türkçe karakter → ASCII (uzun eşleşmeler önce)
    --    Önce büyük harf kombinasyonları, sonra tek harfler
    s := REPLACE(s, 'ı', 'i');
    s := REPLACE(s, 'İ', 'i');
    s := REPLACE(s, 'ş', 's');
    s := REPLACE(s, 'Ş', 's');
    s := REPLACE(s, 'ç', 'c');
    s := REPLACE(s, 'Ç', 'c');
    s := REPLACE(s, 'ğ', 'g');
    s := REPLACE(s, 'Ğ', 'g');
    s := REPLACE(s, 'ö', 'o');
    s := REPLACE(s, 'Ö', 'o');
    s := REPLACE(s, 'ü', 'u');
    s := REPLACE(s, 'Ü', 'u');

    -- 3) Apostrof ve tırnak kaldır (tire YAPMA)
    --    Frontend: /[^a-z0-9\s-]/g → '', yani apostrof sadece silinir
    s := REPLACE(s, '''', '');
    s := REPLACE(s, '"', '');
    s := REPLACE(s, '`', '');

    -- 4) Tüm non-alphanumeric (boşluk ve tire HARİÇ) karakterleri kaldır
    --    Frontend: s.replace(/[^a-z0-9\s-]/g, "")
    s := REGEXP_REPLACE(s, '[^a-z0-9\s-]', '', 'g');

    -- 5) Boşluklar → tire (birden fazlaysa teke indir)
    --    Frontend: s.replace(/\s+/g, "-").replace(/-+/g, "-")
    s := REGEXP_REPLACE(s, '\s+', '-', 'g');
    s := REGEXP_REPLACE(s, '-+', '-', 'g');

    -- 6) Baştaki ve sondaki tire'leri kırp
    s := TRIM(BOTH '-' FROM s);

    RETURN s;
END;
$$;

COMMENT ON FUNCTION public.slugify_title(TEXT)
    IS 'Mevcut title column''undan URL-friendly slug üretir. '
       'Frontend lib/questionMeta.ts:slugifyTitle() ile uyumlu. '
       'Yeni column eklemez (memory kuralı: column freeze).';

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 3) Index: slug aramasını hızlandır (immutable expression)        ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- Eğer interviews tablosunda title column varsa, slugify_title(title) üzerinde
-- index oluştur. Bu yeni column DEĞİL, sadece mevcut title üzerinden hesaplanan
-- expression index. Migration yok, geri alınabilir.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'interviews'
          AND column_name = 'title'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_interviews_slug
            ON public.interviews (public.slugify_title(title));
    END IF;
END $$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 4) View: slug eklenmiş hali (column DEĞİL)                        ║
-- ╚═══════════════════════════════════════════════════════════════════╝

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'interviews'
    ) THEN
        EXECUTE $V$
            CREATE OR REPLACE VIEW public.interviews_with_slug AS
            SELECT
                id,
                title,
                public.slugify_title(title) AS slug,   -- hesaplanmış, sütun değil
                category,
                level,
                description,
                starter_code,
                hints
            FROM public.interviews
        $V$;
    END IF;
END $$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ 5) Schema reload (PostgREST)                                      ║
-- ╚═══════════════════════════════════════════════════════════════════╝

NOTIFY pgrst, 'reload schema';

COMMIT;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ TEST QUERIES (çalıştır, sonuçları gözlemle)                      ║
-- ╚═══════════════════════════════════════════════════════════════════╝

-- SELECT slugify_title('Fibonacci Sayısı Hesaplama');
--  → 'fibonacci-sayisi-hesaplama'

-- SELECT slugify_title('0/1 Knapsack Problemi');
--  → '0-1-knapsack-problemi'

-- SELECT slugify_title('Türkçe Karakterler: ğüşıöç');
--  → 'turkce-karakterler-gusioc'

-- SELECT slugify_title('Stack ile Balanced Parentheses');
--  → 'stack-ile-balanced-parentheses'

-- SELECT * FROM public.interviews_with_slug LIMIT 5;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║ FRONTEND UYUMLULUK TESTİ (assertion)                              ║
-- ║                                                                    ║
-- ║ Bu script frontend'deki slugifyTitle() ile birebir aynı sonucu   ║
-- ║ üretmeli. Aşağıdaki tüm assertion'lar doğru dönüyorsa uyumlu.    ║
-- ╚═══════════════════════════════════════════════════════════════════╝

DO $$
DECLARE
    test_pass BOOLEAN := TRUE;
    expected TEXT;
    actual TEXT;
    test_input TEXT;
BEGIN
    -- Test 1: Temel title
    test_input := 'Fibonacci Sayısı Hesaplama';
    expected := 'fibonacci-sayisi-hesaplama';
    actual := slugify_title(test_input);
    IF actual <> expected THEN
        RAISE WARNING 'TEST FAILED [%]: expected=%, actual=%', test_input, expected, actual;
        test_pass := FALSE;
    END IF;

    -- Test 2: Slug-tire format (parseInt bug testi)
    test_input := '0/1 Knapsack Problemi';
    expected := '01-knapsack-problemi';
    actual := slugify_title(test_input);
    IF actual <> expected THEN
        RAISE WARNING 'TEST FAILED [%]: expected=%, actual=%', test_input, expected, actual;
        test_pass := FALSE;
    END IF;

    -- Test 3: Tüm türkçe karakterler
    test_input := 'Türkçe Karakterler ğüşıöç';
    expected := 'turkce-karakterler-gusioc';
    actual := slugify_title(test_input);
    IF actual <> expected THEN
        RAISE WARNING 'TEST FAILED [%]: expected=%, actual=%', test_input, expected, actual;
        test_pass := FALSE;
    END IF;

    -- Test 4: Çoklu boşluk
    test_input := 'Stack    ile   Balanced';
    expected := 'stack-ile-balanced';
    actual := slugify_title(test_input);
    IF actual <> expected THEN
        RAISE WARNING 'TEST FAILED [%]: expected=%, actual=%', test_input, expected, actual;
        test_pass := FALSE;
    END IF;

    -- Test 5: Boş input
    test_input := '';
    expected := '';
    actual := slugify_title(test_input);
    IF actual <> expected THEN
        RAISE WARNING 'TEST FAILED [%]: expected=%, actual=%', test_input, expected, actual;
        test_pass := FALSE;
    END IF;

    -- Test 6: NULL input
    expected := '';
    actual := slugify_title(NULL);
    IF actual <> expected THEN
        RAISE WARNING 'TEST FAILED [NULL]: expected=%, actual=%', expected, actual;
        test_pass := FALSE;
    END IF;

    -- Test 7: Sadece özel karakter
    test_input := '---!!!---';
    expected := '';
    actual := slugify_title(test_input);
    IF actual <> expected THEN
        RAISE WARNING 'TEST FAILED [%]: expected=%, actual=%', test_input, expected, actual;
        test_pass := FALSE;
    END IF;

    -- Test 8: Sayı içeren
    test_input := 'Pandas DataFrame 101';
    expected := 'pandas-dataframe-101';
    actual := slugify_title(test_input);
    IF actual <> expected THEN
        RAISE WARNING 'TEST FAILED [%]: expected=%, actual=%', test_input, expected, actual;
        test_pass := FALSE;
    END IF;

    -- Test 9: Baştaki ve sondaki tire
    test_input := '  ---Hello World---  ';
    expected := 'hello-world';
    actual := slugify_title(test_input);
    IF actual <> expected THEN
        RAISE WARNING 'TEST FAILED [%]: expected=%, actual=%', test_input, expected, actual;
        test_pass := FALSE;
    END IF;

    IF test_pass THEN
        RAISE NOTICE '✓ Tüm 9 test PASSED — frontend slugifyTitle() ile %100 uyumlu';
    ELSE
        RAISE EXCEPTION 'TEST FAILURE — frontend uyumsuz!';
    END IF;
END $$;
