FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları (psycopg2-binary için gerekli değil, ama curl/sql için)
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıkları
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "supabase>=2.0.0" \
    "resend>=2.0.0" \
    "uvicorn[standard]>=0.27.0" \
    "pydantic[email]>=2.5.0" \
    "fastapi[standard]>=0.110.0" \
    "email-validator>=2.0.0" \
    "requests>=2.31.0" \
    "python-dotenv>=1.0.0" \
    "httpx>=0.26.0" \
    "python-multipart>=0.0.6" \
    "pyjwt>=2.8.0" \
    "google-generativeai>=0.3.0" \
    "gunicorn>=21.2.0" \
    "psycopg2-binary>=2.9.9"

# Uygulama dosyaları
COPY . .

# Port
EXPOSE 8000

# Çalıştır
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]