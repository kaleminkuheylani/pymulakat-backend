# 🐍 PythonMulakat — Backend

Python mülakat hazırlık platformu — FastAPI + Supabase.

## ✨ Özellikler

- 🔐 **Auth** — Supabase ile sign up, login, email verification (6 haneli kod), magic link
- 🐍 **Soru yönetimi** — Kategori bazlı sorular, başlangıç kodu, test case'ler
- 🧪 **Attempt tracking** — Kullanıcı denemeleri, başarı oranı, puan hesaplama
- 📧 **Email** — Resend ile doğrulama kodu gönderimi

## 🚀 Hızlı Başlangıç

```bash
# uv önerilir (proje pyproject.toml ile uyumlu)
uv sync
cp .env.example .env
# .env'i düzenle, gerçek key'leri yaz

uv run uvicorn main:app --reload --port 8000
```

ya da pip ile:
```bash
pip install -r requirements.txt   # pyproject.toml'dan generate et: uv pip compile pyproject.toml
cp .env.example .env
uvicorn main:app --reload --port 8000
```

API: http://localhost:8000
Docs: http://localhost:8000/docs

## 🏗️ Stack

| Teknoloji | Versiyon |
|---|---|
| Python | 3.14+ |
| FastAPI | latest |
| Supabase | latest |
| Resend | latest |
| Pydantic | v2 |

## 📂 Yapı

```
backend/
├── main.py                       # FastAPI app + router mount
├── supabase_client.py            # Anon + admin client factory
├── dependencies.py               # Auth dependency (get_current_user)
├── schemas.py                    # Pydantic şemaları
├── question_loader.py
│
├── routers/
│   ├── auth.py                   # /auth/register, /auth/login, /auth/verify-email, /auth/me
│   ├── questions.py              # /api/v2/questions, /api/v2/questions/{id}/tests
│   ├── categories.py             # /api/v2/categories
│   ├── interviews.py             # /api/v2/interviews
│   └── attempts.py               # /api/v2/attempts
│
├── services/
│   └── upload_questions.py       # Toplu soru yükleme
│
├── models/
│   └── models.py                 # DB modelleri
│
└── data/
    └── QUESTIONS.py              # Statik soru havuzu (varsa)
```

## 🔐 Auth Endpoint'leri

- `POST /auth/register` — Kayıt + email doğrulama kodu gönder
- `POST /auth/login` — Email + şifre ile giriş
- `POST /auth/verify-email` — 6 haneli kodu doğrula
- `POST /auth/resend-code` — Yeni kod gönder
- `GET  /auth/me` — Mevcut kullanıcı + stats

## 🧪 Test Endpoint'leri

- `GET  /api/v2/questions` — Kategori/level filtresiyle soru listesi
- `GET  /api/v2/questions/{id}` — Tek soru detayı
- `GET  /api/v2/questions/{id}/tests` — Test case'ler (auth zorunlu)
- `GET  /api/v2/questions/{id}/progress` — Kullanıcının ilerlemesi
- `POST /api/v2/attempts` — Deneme sonucunu kaydet
- `GET  /api/v2/attempts?limit=N` — Son denemeler
- `GET  /api/v2/attempts/stats` — Kullanıcı istatistikleri

## 🚢 Deploy

**Railway / Fly.io / Render** gibi platformlar için:
1. Repo'yu bağla
2. Environment variables'ı `.env.example`'ten kopyala
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## 📜 Lisans

MIT