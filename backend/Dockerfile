FROM python:3.12-slim AS base

WORKDIR /app

# Fonts to draw the tables of the Excel export
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# The corporate proxy re-signs HTTPS with a self-signed cert; skip TLS verification for pip
# at build time only (same as npm_config_strict_ssl=false in frontend/Dockerfile).
ARG PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org"

# Install Python deps first (layer cache)
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir ".[dev]" && pip install --no-cache-dir uvicorn

# Copy reqmap package (node parsing and client of the pdf2md server)
COPY reqmap /app/reqmap

# Copy backend application
COPY backend/app /app/app

# Copy customer config
COPY config /app/config

# Runtime env defaults (override via docker-compose or .env)
ENV DATABASE_URL="sqlite+aiosqlite:///./data/reqmap.db" \
    UPLOAD_DIR="/app/uploads" \
    CUSTOMERS_CONFIG_PATH="/app/config/customers.json" \
    PYTHONUNBUFFERED=1

RUN mkdir -p /app/data /app/uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
