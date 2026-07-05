FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıkları (requirements.txt)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyaları
COPY . .

# Vercel @vercel/docker runtime PORT env üzerinden çalışır (default 3000)
ENV PORT=3000
EXPOSE 3000

# Çalıştır — main.py "app" değişkenini export ediyor
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
