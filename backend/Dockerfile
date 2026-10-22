FROM python:3.12-slim AS base

WORKDIR /app

# System deps needed by pymupdf / OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer cache)
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir ".[dev]" && pip install --no-cache-dir uvicorn

# Heavy pdf2md engines (docling, marker) with the CPU build of torch (the default
# PyPI wheel is the multi-GB NVIDIA build). Kept before the source COPYs for layer cache.
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
        --extra-index-url https://pypi.org/simple \
    && pip install --no-cache-dir "docling>=2.140" "marker-pdf>=2.0"

# Copy reqmap package (node parsing) and the pdf2md submodule (PDF to markdown;
# the package lives in pdf2md/src, added to sys.path by reqmap.pdf_source)
COPY reqmap /app/reqmap
COPY pdf2md /app/pdf2md

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
