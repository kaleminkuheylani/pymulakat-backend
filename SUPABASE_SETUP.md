# Supabase Dashboard Ayarları

Tüm auth akışlarının çalışması için Supabase Dashboard'da şu ayarlar gerekli.

## 1. Authentication → URL Configuration

**Site URL:**
```
https://www.pythonmulakat.com
```

**Redirect URLs** (hepsini ekle):
```
http://localhost:3000/auth/callback
http://localhost:3000/auth/reset-password
https://www.pythonmulakat.com/auth/callback
https://www.pythonmulakat.com/auth/reset-password
https://pymulakat-frontend.vercel.app/auth/callback
https://pymulakat-frontend.vercel.app/auth/reset-password
```

## 2. Authentication → Providers

| Provider | Durum | Açıklama |
|----------|------|----------|
| **Email** | ✅ Açık | Magic link + şifre sıfırlama için zorunlu |
| Google | 🔘 İsteğe bağlı | OAuth giriş için |
| GitHub | 🔘 İsteğe bağlı | OAuth giriş için |
| Apple | 🔘 İsteğe bağlı | OAuth giriş için |

## 3. Authentication → Email Templates

### Confirm signup
- **Subject:** `🐍 PythonMulakat — Hesabını doğrula`
- **Redirect to:** `{{ .SiteURL }}/auth/callback?type=signup&returnUrl=/interviews`
- Body (HTML örneği):
```html
<h2>Hoş geldin!</h2>
<p>Hesabını aktifleştirmek için aşağıdaki linke tıkla:</p>
<p><a href="{{ .ConfirmationURL }}">Hesabımı Doğrula</a></p>
```

### Reset Password
- **Subject:** `🐍 PythonMulakat — Şifre sıfırlama`
- **Redirect to:** `{{ .SiteURL }}/auth/callback?type=recovery&returnUrl=/auth/reset-password`
- Body:
```html
<h2>Şifre sıfırlama</h2>
<p>Yeni şifre belirlemek için aşağıdaki linke tıkla:</p>
<p><a href="{{ .ConfirmationURL }}">Şifremi Sıfırla</a></p>
<p>Bu link 1 saat geçerlidir.</p>
```

### Magic Link
- **Subject:** `🐍 PythonMulakat — Giriş linkin`
- **Redirect to:** `{{ .SiteURL }}/auth/callback?type=magiclink`
- Body:
```html
<h2>Giriş</h2>
<p>Aşağıdaki linke tıklayarak giriş yap:</p>
<p><a href="{{ .ConfirmationURL }}">Giriş Yap</a></p>
<p>Bu link 1 saat geçerlidir.</p>
```

## 4. SQL Editor — profiles tablosu

```sql
-- profiles tablosu (Supabase auth.users'a bağlı)
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  is_verified BOOLEAN DEFAULT FALSE,
  points INT DEFAULT 0,
  verification_code TEXT,
  verification_code_expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

-- interview_attempts tablosu
CREATE TABLE IF NOT EXISTS public.interview_attempts (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  question_id INT NOT NULL,
  passed_tests INT NOT NULL DEFAULT 0,
  total_tests INT NOT NULL DEFAULT 0,
  success BOOLEAN NOT NULL DEFAULT FALSE,
  execution_time_ms INT NOT NULL DEFAULT 0,
  hints_used INT NOT NULL DEFAULT 0,
  user_code TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_attempts_user_id ON interview_attempts(user_id);
CREATE INDEX idx_attempts_question_id ON interview_attempts(question_id);

ALTER TABLE interview_attempts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own attempts" ON interview_attempts
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own attempts" ON interview_attempts
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- questions tablosu (örnek yapı)
CREATE TABLE IF NOT EXISTS public.questions (
  id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL,
  level TEXT NOT NULL DEFAULT 'beginner',
  function_name TEXT NOT NULL,
  starter_code TEXT,
  test_cases JSONB NOT NULL DEFAULT '[]'::jsonb,
  tags TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_questions_category ON questions(category);
CREATE INDEX idx_questions_level ON questions(level);

ALTER TABLE questions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view questions" ON questions
  FOR SELECT USING (true);
```

## 5. Backend Environment Variables

Railway'de şu değişkenler tanımlı olmalı:

```bash
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
RESEND_API_KEY=<resend-api-key>
RESEND_FROM_EMAIL=mkemal@pythonmulakat.com
APP_ENV=production
CORS_ORIGINS=https://www.pythonmulakat.com,https://pymulakat-frontend.vercel.app
```

## 6. Frontend Environment Variables

Vercel'de şu değişkenler tanımlı olmalı:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>
NEXT_PUBLIC_API_URL=https://<railway-app>.up.railway.app
```

---

## Akış Özeti

| Adım | Endpoint / Sayfa | Yöntem |
|------|------------------|--------|
| Kayıt ol | `POST /auth/register` | Backend (FastAPI) |
| Email doğrulama | `POST /auth/verify-email` | Backend (6 haneli kod) |
| Kod yeniden gönder | `POST /auth/resend-code` | Backend |
| Şifre ile giriş | `POST /auth/login` | Backend |
| Magic link giriş | `supabase.auth.signInWithOtp()` | Frontend (Supabase) |
| OAuth (Google/GitHub) | `supabase.auth.signInWithOAuth()` | Frontend (Supabase) |
| Şifremi unuttum | `supabase.auth.resetPasswordForEmail()` | Frontend (Supabase) |
| Şifre sıfırla | `supabase.auth.updateUser({password})` | Frontend (Supabase) |
| Çıkış | `POST /auth/logout` + localStorage temizleme | Backend + Frontend |
| Profil bilgisi | `GET /auth/me` | Backend |