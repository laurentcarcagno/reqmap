# ReqMap — Model Context

## What is ReqMap?

ReqMap is a full-stack web application that converts PDF requirement documents into structured, reviewable JSON nodes. Users upload a PDF, select their customer extractor, and then review extracted **title** and **requirement** nodes with editable **Applicability** and **Conformity** attributes.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15, React 19, Tailwind CSS, TanStack Query, Sonner, react-dropzone |
| **Backend** | FastAPI (Python 3.12), SQLAlchemy 2 async, aiosqlite, Pydantic v2, Uvicorn |
| **Database** | SQLite (MVP) via `aiosqlite` |
| **Extraction** | `pdf2md` (git submodule) for PDF → markdown, `reqmap.parse_nodes` for markdown → nodes |
| **Containerization** | Docker + Docker Compose |

---

## Project Structure

```
ReqMap/
├── reqmap/                  # Python extraction tools (refactored for configurable patterns)
│   ├── pdf_source.py        # pdf_to_markdown() — wraps the pdf2md submodule
│   ├── node_parser.py       # parse_nodes() — markdown → title/requirement nodes
│   └── tests/
│       └── test_node_parser.py
├── pdf2md/                  # git submodule (laurentcarcagno/pdf2md) — PDF → markdown
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app entry + lifespan
│   │   ├── config.py        # Pydantic Settings (env vars)
│   │   ├── database.py      # SQLAlchemy async engine + session
│   │   ├── models/          # ORM: Document, Node
│   │   ├── routers/         # health, customers, documents, nodes
│   │   ├── services/        # customer_config, document_service, processing_service
│   │   ├── repositories/    # document_repository, node_repository
│   │   └── schemas/         # Pydantic: customer, document, node
│   ├── tests/               # pytest-asyncio tests
│   ├── pyproject.toml
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router
│   │   ├── components/
│   │   │   ├── layout/      # AppShell, Header, Sidebar
│   │   │   └── features/
│   │   │       ├── upload/  # UploadDialog
│   │   │       ├── documents/ # DocumentList, DocumentCard, DocumentViewer
│   │   │       └── nodes/   # NodeTable, ApplicabilitySelect, ConformitySelect
│   │   ├── lib/             # api.ts (typed API client), utils.ts
│   │   └── styles/          # globals.css (CSS custom properties — design tokens)
│   ├── package.json
│   └── Dockerfile
├── config/
│   └── customers.json       # Customer extractor config (id → label + regex patterns)
├── docker-compose.yml       # Production
├── docker-compose.dev.yml   # Development with hot reload
└── model-context.md         # This file
```

---

## Key Design Decisions

### Centralized Theming
All colors, spacing, radii use CSS custom properties in `src/styles/globals.css`. Light and dark themes are defined there. Components reference tokens only — never hardcoded values.

### Customer-Configurable Extractors
`config/customers.json` maps a customer ID (`"airbus"`) to:
- `label` — display name
- `req_id_pattern` — regex for requirement ID lines (group 1 = ID, group 2 = title)
- `title_pattern` — optional override for numbered heading detection
- `noise_patterns` — list of regex strings for lines to discard

The `parse_nodes()` function accepts these as keyword arguments, defaulting to Airbus patterns for backward compatibility.

### Default Node Values
| Node type | Applicability | Conformity |
|-----------|--------------|------------|
| `requirement` | `A` | `C` |
| `title` | `T` | `T` |

### Applicability values: `NA`, `A`, `A/M`, `TBC`, `T`
### Conformity values: `NA`, `C`, `C TBC`, `PC`, `NC`, `TBC`, `T`

### Tables as images
PDF tables are kept as pictures of their page area (pdf2md `--tables-as-images`), stored with the document's other figures and referenced from the node descriptions. Backend setting `TABLES_AS_IMAGES` (default `1` = tables of at least 1 row; empty = keep tables as Markdown text). Existing documents must be re-imported to benefit.

### Background Processing
Document processing runs as a FastAPI `BackgroundTask`. It opens its own `AsyncSessionLocal` sessions — never shares the request-scoped session.

---

## API Endpoints (v1)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/customers` | List configured customers |
| `POST` | `/api/v1/documents` | Upload document (multipart: `file` + `customer`) |
| `GET` | `/api/v1/documents` | List documents |
| `GET` | `/api/v1/documents/{id}` | Get document by ID |
| `GET` | `/api/v1/documents/{id}/nodes` | List nodes for a document |
| `GET`/`PUT` | `/api/v1/documents/{id}/export-settings` | Values of the Excel matrix not deducible from the PDF (project, edition, signatories, AD/RD/acronym tables…), saved per document |
| `GET` | `/api/v1/documents/{id}/export` | Excel compliance matrix filled into `config/templates/HMA-C-049_EdC_Matrice-Conformite-Exigences.xlsx` |
| `PATCH` | `/api/v1/nodes/{id}` | Update node applicability/conformity/comment |

Interactive docs: `http://localhost:8000/api/docs`

---

## Running Locally (without Docker)

**Backend:**
```bash
cd backend
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Tests:**
```bash
python -m pytest backend/tests/ -v
python -m pytest reqmap/tests/ -v
```

---

## Running with Docker

```bash
# Production
docker compose up --build

# Development (hot reload)
docker compose -f docker-compose.dev.yml up --build
```

---

## Adding a New Customer

1. Edit `config/customers.json`
2. Add an entry:
```json
{
  "customers": {
    "my_customer": {
      "label": "My Customer",
      "req_id_pattern": "^(MC-REQ-\\d+)\\s*/\\s*(.+)$",
      "title_pattern": null,
      "noise_patterns": ["^\\s*CONFIDENTIAL\\s*$"]
    }
  }
}
```
3. The customer appears in the upload dialog dropdown immediately.

A customer can also run pdf2md post-processing plugins (the equivalent of `pdf2md --post-process NAME`) on the
converted markdown, with `"post_process": {"Plugin name": "pdf2md/examples/plugins/script.py"}` (name → script path
relative to the repo root, run in order). `tas` (Thales Alénia Space) uses this to mark `#ID Title … ##` requirements.

---

## Development Roadmap

- **Release 1.0 (MVP):** Upload, Process, Review — ✅ In progress
- **Release 1.1:** Multi-user auth (JWT), real-time collaboration (WebSockets)
- **Release 1.2:** DOCX support, export (CSV; Excel matrix already available), audit trail
- **Release 2.0:** White-label theming, customer admin panel, CI/CD
