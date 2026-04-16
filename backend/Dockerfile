FROM python:3.12-slim AS base

WORKDIR /app

# System deps needed by pymupdf / OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer cache)
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir ".[dev]" && pip install --no-cache-dir uvicorn

# Copy reqmap package (extraction tools)
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
