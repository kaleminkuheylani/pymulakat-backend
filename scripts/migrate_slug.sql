-- ═══════════════════════════════════════════════════════════
-- SLUG KOLONU EKLEME — interviews tablosu
-- Canonical URL pattern: /interviews/{cat}/{slug}
-- ═══════════════════════════════════════════════════════════

ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS slug TEXT;

-- Unique index (her slug tek olmalı)
CREATE UNIQUE INDEX IF NOT EXISTS idx_interviews_slug ON public.interviews(slug) WHERE slug IS NOT NULL;

-- Schema cache invalidate
NOTIFY pgrst, 'reload schema';