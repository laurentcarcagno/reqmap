# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

ReqMap is a three-layer system that turns requirement-document PDFs into reviewable structured nodes:

1. **`reqmap/`** — a standalone Python library that extracts a PDF → clean markdown → ordered list of `title` and `requirement` nodes. Can be used via CLI (`python -m reqmap`) or imported.
2. **`backend/`** — a FastAPI service that wraps the `reqmap` library, persists results to SQLite, and exposes a REST API.
3. **`frontend/`** — a Next.js 15 / React 19 UI for uploading PDFs, picking a customer extractor, and reviewing/editing the resulting nodes.

The backend imports `reqmap` directly from the repo root (see `_ensure_reqmap_importable` in [backend/app/services/processing_service.py](backend/app/services/processing_service.py) — it injects the project root onto `sys.path`). `reqmap/` is **not** an installed dependency of the backend; they live in the same tree and share source.

## Commands

All Python commands assume Python 3.12+. Run from the repo root unless noted.

**Backend (FastAPI):**
```bash
cd backend && pip install -e ".[dev]"
cd backend && uvicorn app.main:app --reload           # dev server on :8000
pytest backend/tests/ -v                               # full backend suite
pytest backend/tests/test_documents.py::test_name -v   # single test
```

**Frontend (Next.js):**
```bash
cd frontend && npm install
cd frontend && npm run dev                             # :3000
cd frontend && npm run build
cd frontend && npm test                                # vitest run (once)
cd frontend && npm run test:watch
```

**reqmap library:**
```bash
pip install -r requirements.txt
python -m reqmap path/to/doc.pdf [--json] [--no-ocr] [--no-clean] [-v]
pytest reqmap/tests/ -v
```

**Docker:**
```bash
docker compose up --build                              # prod: backend :8090, frontend :3000
docker compose -f docker-compose.dev.yml up --build    # dev: backend :8008, hot reload both
```

Interactive API docs: `http://localhost:8000/api/docs` (or `:8090` in prod compose).

## Architecture highlights

### The pipeline
`PDF → PDFExtractor.extract() → (raw_md, clean_md) → parse_nodes(clean_md) → [{order,type,section?,req_id?,title,description}, ...]`

- [reqmap/extractor.py](reqmap/extractor.py) orchestrates: pymupdf4llm extraction → header/footer removal → inline-image OCR injection → markdown cleaning.
- [reqmap/node_parser.py](reqmap/node_parser.py) walks the cleaned markdown and emits nodes. **Patterns are parameterized** (`req_id_pattern`, `title_pattern`, `noise_patterns`) and default to Airbus-specific values when not supplied.

### Customer-configurable extractors
[config/customers.json](config/customers.json) maps a customer id → `{label, req_id_pattern, title_pattern, noise_patterns}`. The frontend populates its upload dropdown from `GET /api/v1/customers`, and `processing_service._run_reqmap` passes the chosen customer's regexes into `parse_nodes`. **To add a customer, edit this JSON only** — no code change needed.

### Backend layering
`routers/` (HTTP) → `services/` (orchestration) → `repositories/` (data access) → `models/` (SQLAlchemy 2 async ORM). Pydantic v2 schemas in `schemas/`. Keep this separation when extending.

### Background processing rule
`process_document` in [backend/app/services/processing_service.py](backend/app/services/processing_service.py) runs as a FastAPI `BackgroundTask`. It **opens its own `AsyncSessionLocal` sessions** and must never share the request-scoped session. Any new background work should follow this pattern — status updates and final persistence use separate sessions with their own `commit()`.

### Schema migration approach
The backend uses SQLAlchemy `create_all` plus a hand-maintained `_DOC_MIGRATIONS` list of idempotent `ALTER TABLE ... ADD COLUMN` statements in [backend/app/main.py](backend/app/main.py:18). Each statement is wrapped in try/except (ignores "column already exists"). When adding a new nullable column to an existing table, append a statement here — Alembic is listed as a dep but not yet wired up.

### Node value enums
These are enforced at both the ORM layer ([backend/app/models/node.py](backend/app/models/node.py)) and the UI:
- `applicability`: `NA`, `A`, `A/M`, `TBC`, `T` (defaults: requirement→`A`, title→`T`)
- `conformity`: `NA`, `C`, `C TBC`, `PC`, `NC`, `TBC`, `T` (defaults: requirement→`C`, title→`T`)

Changing these values means touching the SQLAlchemy `Enum`, the Pydantic schemas, and the frontend select components together.

### Frontend design tokens
All colors/spacing/radii are CSS custom properties in `frontend/src/styles/globals.css`. Light and dark themes defined there. Components reference tokens — never hardcode values.

## Conventions

- **Conventional Commits** (`feat(scope): ...`, `fix: ...`, `refactor: ...`, etc.) — see recent git log for examples. Commit message body explains *why*, not *what*.
- **Python:** type hints on all signatures; Pydantic v2 models for every request/response schema.
- **TypeScript:** strict mode. Functional React components only; minimize `useEffect`; use TanStack Query for server state.
- **Tests:** `pytest-asyncio` in `auto` mode for backend (see [backend/pyproject.toml](backend/pyproject.toml)); vitest + jsdom for frontend.
- Do **not** commit `.env` (use `.env.example`). Do not commit the `data/` SQLite file or `uploads/`.

## Roadmap context (from [model-context.md](model-context.md))
- 1.0 MVP (current): upload → process → review
- 1.1: JWT auth, WebSocket collaboration (JWT settings already stubbed in [backend/app/config.py](backend/app/config.py))
- 1.2: DOCX support, CSV/Excel export, audit trail
