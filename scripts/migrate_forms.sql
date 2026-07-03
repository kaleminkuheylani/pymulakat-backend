-- Migration: Forms + Form Replies (topluluk özelliği)
-- 2026-07-03

-- 1) Forms tablosu
CREATE TABLE IF NOT EXISTS public.forms (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  category TEXT NOT NULL CHECK (category IN ('feedback', 'question_help', 'code_help', 'share')),
  title TEXT NOT NULL CHECK (length(title) BETWEEN 3 AND 120),
  body TEXT NOT NULL CHECK (length(body) BETWEEN 10 AND 5000),
  tags TEXT[] DEFAULT '{}',
  related_question_id BIGINT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_forms_user_id ON public.forms(user_id);
CREATE INDEX IF NOT EXISTS idx_forms_category ON public.forms(category);
CREATE INDEX IF NOT EXISTS idx_forms_created_at ON public.forms(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_forms_related_q ON public.forms(related_question_id) WHERE related_question_id IS NOT NULL;

-- 2) Form Replies (yanıtlar)
CREATE TABLE IF NOT EXISTS public.form_replies (
  id BIGSERIAL PRIMARY KEY,
  form_id BIGINT NOT NULL REFERENCES public.forms(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  body TEXT NOT NULL CHECK (length(body) BETWEEN 2 AND 2000),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_form_replies_form_id ON public.form_replies(form_id, created_at);

-- 3) RLS (Row Level Security)
ALTER TABLE public.forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.form_replies ENABLE ROW LEVEL SECURITY;

-- Forms: Herkes okuyabilir, sadece giriş yapmış user insert edebilir
DROP POLICY IF EXISTS "forms_read_all" ON public.forms;
CREATE POLICY "forms_read_all" ON public.forms FOR SELECT USING (true);

DROP POLICY IF EXISTS "forms_insert_authenticated" ON public.forms;
CREATE POLICY "forms_insert_authenticated" ON public.forms FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "forms_update_own" ON public.forms;
CREATE POLICY "forms_update_own" ON public.forms FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "forms_delete_own" ON public.forms;
CREATE POLICY "forms_delete_own" ON public.forms FOR DELETE USING (auth.uid() = user_id);

-- Replies: Herkes okuyabilir, sadece giriş yapmış user insert edebilir
DROP POLICY IF EXISTS "form_replies_read_all" ON public.form_replies;
CREATE POLICY "form_replies_read_all" ON public.form_replies FOR SELECT USING (true);

DROP POLICY IF EXISTS "form_replies_insert_authenticated" ON public.form_replies;
CREATE POLICY "form_replies_insert_authenticated" ON public.form_replies FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "form_replies_delete_own" ON public.form_replies;
CREATE POLICY "form_replies_delete_own" ON public.form_replies FOR DELETE USING (auth.uid() = user_id);

-- 4) updated_at trigger
CREATE OR REPLACE FUNCTION public.touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_forms_touch ON public.forms;
CREATE TRIGGER trg_forms_touch
  BEFORE UPDATE ON public.forms
  FOR EACH ROW
  EXECUTE FUNCTION public.touch_updated_at();