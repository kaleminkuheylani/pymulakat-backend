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
ENV PORT=3000
EXPOSE 3000

# Çalıştır — main.py "app" değişkenini export ediyor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
