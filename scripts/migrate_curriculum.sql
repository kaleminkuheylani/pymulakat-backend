-- ═══════════════════════════════════════════════════════════
-- 84 GÜNLÜK MÜFREDAT KONSEPTİ
-- Yeni: interviews.day/week/theme/difficulty + curriculum tablosu
-- ═══════════════════════════════════════════════════════════

-- 1. interviews'a yeni kolonlar
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS day INT;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS week INT;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS theme TEXT;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS difficulty INT DEFAULT 1;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS curriculum_slug TEXT;

-- Indexes (curriculum bazlı sorgular için)
CREATE INDEX IF NOT EXISTS idx_interviews_week ON public.interviews(week);
CREATE INDEX IF NOT EXISTS idx_interviews_day ON public.interviews(day);
CREATE INDEX IF NOT EXISTS idx_interviews_difficulty ON public.interviews(difficulty);
CREATE INDEX IF NOT EXISTS idx_interviews_curriculum_slug ON public.interviews(curriculum_slug) WHERE curriculum_slug IS NOT NULL;

-- 2. curriculum tablosu (84 günlük plan)
CREATE TABLE IF NOT EXISTS public.curriculum (
  id BIGSERIAL PRIMARY KEY,
  day INT UNIQUE NOT NULL,
  week INT NOT NULL,
  topic TEXT NOT NULL,
  category TEXT NOT NULL,
  level TEXT DEFAULT 'beginner',
  theme TEXT,
  difficulty INT DEFAULT 1,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_curriculum_week ON public.curriculum(week);
CREATE INDEX IF NOT EXISTS idx_curriculum_category ON public.curriculum(category);

-- 3. RLS — herkes okuyabilsin (public)
ALTER TABLE public.curriculum ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can read curriculum" ON public.curriculum;
CREATE POLICY "Anyone can read curriculum" ON public.curriculum
  FOR SELECT USING (true);

DROP POLICY IF EXISTS "Service role full access to curriculum" ON public.curriculum;
CREATE POLICY "Service role full access to curriculum" ON public.curriculum
  FOR ALL USING (auth.role() = 'service_role');

-- 4. PostgREST cache invalidate
NOTIFY pgrst, 'reload schema';