FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# uv (pinned, official image)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Layer cache: dependency kurulumu önce (pyproject + lock değişmedikçe cache)
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --no-install-project

# Source
COPY . .
RUN uv sync --no-dev

# venv python PATH'e ekle
ENV PATH="/app/.venv/bin:$PATH"

# PORT env'i Railway tarafından runtime'da inject edilir; hardcoded olmasın
# (Railway dashboard → Variables'da PORT override edilebilir)
EXPOSE 3000

# Çalıştır — main.py "app" değişkenini export ediyor.
# PORT env Railway tarafından runtime'da sağlanır (default 3000).
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-3000}"]
