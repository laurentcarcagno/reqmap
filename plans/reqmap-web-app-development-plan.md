# ReqMap Web Application — Development Plan

Build a full-stack web application (FastAPI backend + Next.js frontend) that wraps the existing `reqmap` Python PDF extraction tools, providing multi-user document processing with real-time collaboration, centralized theming, and customer-configurable extractors.

---

**Created:** 2026-04-16
**Last Updated:** 2026-04-16
**Status:** Draft

---

## Assumptions & Decisions

1. **Backend:** FastAPI (Python) — natural fit since `reqmap` is Python; direct import of existing extraction tools.
2. **Frontend:** Next.js 14+ (App Router) + React + Tailwind CSS + shadcn/ui.
3. **Database:** SQLite (confirmed) — SQLAlchemy + Alembic for ORM/migrations.
4. **Auth:** JWT-based multi-user authentication (HS256 for MVP).
5. **Real-time:** WebSocket via FastAPI for presence and live node edits.
6. **Customer config:** JSON file mapping customer name → extractor regex patterns and noise filters.
7. **Refactor `reqmap/node_parser.py`** (confirmed) — make it accept configurable regex patterns instead of hardcoded Airbus-specific values. Current Airbus patterns become the default config entry.
8. **Docker containerization** (confirmed) — Dockerfile + docker-compose for backend, frontend, and development workflow.
9. Single dev team, 2-week sprints.

---

## Release Map

| Release | Title | Sprints | Focus |
|---------|-------|---------|-------|
| **1.0** | MVP — Upload, Process & Review | 1–5 | Backend API, DB, frontend shell, file upload, PDF processing, node viewer with Applicability/Conformity, Docker |
| **1.1** | Multi-User & Collaboration | 6–8 | Auth, multi-user, real-time sync, presence, role-based rendering |
| **2.0** | Multi-Customer & Polish | 9–11 | Customer-configurable extractors, theme switching, DOCX support, accessibility, i18n prep |

---

## Release 1.0 — MVP: Upload, Process & Review

**Goal:** A single-user web app where the user can upload a PDF, process it via the `reqmap` pipeline, browse processed documents, view extracted nodes, and set Applicability/Conformity values per node.

**Target:** Sprint 1–5 (10 weeks)

---

### Sprint 1 — Project Scaffolding & Database

**Sprint Goal:** Set up the backend (FastAPI) and frontend (Next.js) projects, establish the database schema, and create the customer configuration file.

---

- [ ] **Task 1.1:** Backend project scaffolding (`@backend-development`)
  **Priority:** High | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] FastAPI app with proper project structure: `backend/app/main.py`, `config.py`, `database.py`
  - [ ] Dependency management via `pyproject.toml` with `uv`
  - [ ] Health check endpoint `GET /api/v1/health` returns `200`
  - [ ] CORS middleware configured for local frontend dev
  - [ ] Structured logging with JSON output

  **Implementation Steps:**
  - [ ] Develop: Create `backend/` directory with FastAPI app structure: `app/main.py`, `app/config.py` (env vars validated with Pydantic Settings), `app/database.py` (SQLAlchemy async engine + session), `app/routers/`, `app/services/`, `app/schemas/`, `app/models/`, `app/middleware/`. Add `pyproject.toml` with dependencies: `fastapi`, `uvicorn`, `sqlalchemy[asyncio]`, `aiosqlite`, `alembic`, `pydantic-settings`, `python-multipart`.
  - [ ] Test: Write `tests/test_health.py` — verify `/api/v1/health` returns 200.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(api): scaffold FastAPI backend with health endpoint`

  **Dependencies:** None

---

- [ ] **Task 1.2:** Database schema — documents and nodes (`@database-management`)
  **Priority:** High | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] `documents` table: `id`, `filename`, `original_filename`, `file_path`, `customer`, `status` (pending/processing/completed/failed), `node_count`, `title_count`, `requirement_count`, `uploaded_by`, `created_at`, `updated_at`
  - [ ] `nodes` table: `id`, `document_id` (FK), `order`, `type` (title/requirement), `section`, `req_id`, `title`, `description`, `applicability`, `conformity`, `updated_by`, `updated_at`
  - [ ] Alembic migration setup with initial migration
  - [ ] Default values: requirement nodes → applicability=`A`, conformity=`C`; title nodes → applicability=`T`, conformity=`T`

  **Implementation Steps:**
  - [ ] Develop: Create SQLAlchemy models in `backend/app/models/document.py` and `backend/app/models/node.py`. Initialize Alembic in `backend/alembic/`. Create migration `001_initial_schema.py`.
  - [ ] Test: Run `alembic upgrade head` and `alembic downgrade -1` and `alembic upgrade head` — verify migrations work.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(db): add documents and nodes tables with Alembic migration`

  **Dependencies:** Task 1.1

---

- [ ] **Task 1.3:** Refactor `reqmap/node_parser.py` for configurable patterns (`@backend-development`)
  **Priority:** High | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] `parse_nodes()` accepts optional `req_id_pattern`, `noise_patterns`, and `title_pattern` parameters
  - [ ] When no patterns provided, defaults to current Airbus-specific patterns (backward compatible)
  - [ ] `_REQ_RE`, `_NOISE_PATTERNS` compiled from parameters at call time instead of module-level constants
  - [ ] Existing CLI (`python -m reqmap`) continues to work unchanged
  - [ ] All existing output remains identical (regression test against `output/` reference files)

  **Implementation Steps:**
  - [ ] Develop: Refactor `reqmap/node_parser.py` — extract hardcoded Airbus regex into default parameter values. Add `req_id_pattern: str | None`, `title_pattern: str | None`, `noise_patterns: list[str] | None` params to `parse_nodes()`. Compile regex from params inside the function. Keep module-level constants as defaults.
  - [ ] Test: Write `reqmap/tests/test_node_parser.py` — regression test comparing output against `output/AD01_..._nodes.json`. Test with custom patterns. Test default (no args) matches original behavior.
  - [ ] Verify: `cd ReqMap && python -m pytest reqmap/tests/` — all tests pass
  - [ ] Commit: `refactor(reqmap): make node_parser accept configurable regex patterns`

  **Dependencies:** None

---

- [ ] **Task 1.4:** Customer extractor configuration file (`@backend-development`)
  **Priority:** High | **Effort:** S (< 2h)

  **Acceptance Criteria:**
  - [ ] `config/customers.json` maps customer name → extractor settings (regex patterns, noise patterns)
  - [ ] `airbus` customer configured with current `node_parser.py` default patterns
  - [ ] Service to load and validate the config at startup
  - [ ] Config is extensible for future customers without code changes

  **Implementation Steps:**
  - [ ] Develop: Create `config/customers.json` with structure: `{ "customers": { "airbus": { "label": "Airbus", "req_id_pattern": "^(HAR\\s+SSOW-\\d+)\\s*/\\s*(.+)$", "noise_patterns": [...] } } }`. Create `backend/app/services/customer_config.py` — load, validate, list customers.
  - [ ] Test: Write `tests/test_customer_config.py` — verify config loads, airbus entry exists, invalid config raises error.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(config): add customer extractor configuration file`

  **Dependencies:** Task 1.3

---

- [ ] **Task 1.5:** Frontend project scaffolding (`@frontend-development`)
  **Priority:** High | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] Next.js 14+ App Router project in `frontend/`
  - [ ] Tailwind CSS configured with design tokens (colors, typography, spacing) in `tailwind.config.ts`
  - [ ] shadcn/ui initialized with base components
  - [ ] CSS Custom Properties for theme switching (single source of truth)
  - [ ] Dark/light mode toggle working via ThemeProvider
  - [ ] App shell layout: sidebar (left panel) + main content (center) + header

  **Implementation Steps:**
  - [ ] Develop: `npx create-next-app@latest frontend --typescript --tailwind --app --src-dir`. Install and configure shadcn/ui. Create `src/styles/globals.css` with CSS custom properties for all design tokens. Create `src/components/layout/app-shell.tsx` (sidebar + main), `src/components/layout/header.tsx`, `src/components/theme-provider.tsx`. Set up `src/lib/api.ts` for API client configuration.
  - [ ] Test: Verify app builds and renders the shell layout with `npm run build`.
  - [ ] Verify: `cd frontend && npm run build` — builds successfully
  - [ ] Commit: `feat(ui): scaffold Next.js frontend with centralized theming and app shell`

  **Dependencies:** None

---

### Sprint 2 — File Upload & PDF Processing API

**Sprint Goal:** Upload PDFs via drag-and-drop or file browser, trigger the `reqmap` pipeline, store results in the database.

---

- [ ] **Task 2.1:** Document upload API endpoint (`@backend-development`)
  **Priority:** High | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] `POST /api/v1/documents/upload` accepts multipart file + `customer` field
  - [ ] Validates file type (PDF only for now, extensible to docx/doc later)
  - [ ] Saves file to `uploads/` directory with unique filename
  - [ ] Creates `documents` DB record with `status=pending`
  - [ ] Returns document metadata (id, filename, status)
  - [ ] File size limit enforced (configurable, default 50MB)

  **Implementation Steps:**
  - [ ] Develop: Create `backend/app/routers/documents.py` with upload endpoint. Create `backend/app/schemas/document.py` with Pydantic request/response models. Create `backend/app/services/document_service.py` — file validation, storage, DB record creation. Create `backend/app/repositories/document_repository.py` — CRUD operations.
  - [ ] Test: Write `tests/test_document_upload.py` — test valid PDF upload, invalid file type rejection, size limit, missing customer field.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(api): add document upload endpoint with validation`

  **Dependencies:** Tasks 1.1, 1.2

---

- [ ] **Task 2.2:** PDF processing service — integrate reqmap pipeline (`@backend-development`)
  **Uses refactored `reqmap/node_parser.py` with customer-specific patterns from config.**
  **Priority:** High | **Effort:** L (4–8h)

  **Acceptance Criteria:**
  - [ ] Background task processes uploaded PDF using `reqmap.extractor.PDFExtractor`
  - [ ] Nodes parsed via `reqmap.node_parser.parse_nodes` (customer-aware in future)
  - [ ] Extracted nodes stored in `nodes` table with correct defaults (title: A=T, C=T; requirement: A=A, C=C)
  - [ ] Document status updated: `pending` → `processing` → `completed` (or `failed` with error message)
  - [ ] Raw markdown, clean markdown, and JSON stored alongside the document

  **Implementation Steps:**
  - [ ] Develop: Create `backend/app/services/processing_service.py` — orchestrates `PDFExtractor.extract()` + `parse_nodes(clean_md, source, req_id_pattern=..., noise_patterns=...)` using customer-specific patterns from config. Saves artifacts, creates node records with defaults. Use FastAPI `BackgroundTasks` for async processing. Create `backend/app/repositories/node_repository.py` — batch insert nodes. Wire into upload endpoint to auto-trigger processing.
  - [ ] Test: Write `tests/test_processing_service.py` — test with a small sample PDF, verify nodes created with correct defaults, verify status transitions.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(api): implement PDF processing service with reqmap pipeline integration`

  **Dependencies:** Tasks 2.1, 1.3, 1.4

---

- [ ] **Task 2.3:** Document list and detail API endpoints (`@backend-development`)
  **Priority:** High | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] `GET /api/v1/documents` — list documents (paginated, cursor-based)
  - [ ] `GET /api/v1/documents/{id}` — document metadata
  - [ ] `GET /api/v1/documents/{id}/nodes` — list nodes for a document (paginated)
  - [ ] Response shapes follow envelope pattern: `{ data, meta }`

  **Implementation Steps:**
  - [ ] Develop: Add list/detail routes to `documents.py` router. Add nodes list route. Create response schemas with pagination meta.
  - [ ] Test: Write `tests/test_document_endpoints.py` — test list, detail, nodes list, pagination, 404 handling.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(api): add document list and node retrieval endpoints`

  **Dependencies:** Task 2.2

---

### Sprint 3 — Frontend: Upload & Document List

**Sprint Goal:** Implement the file upload component (drag-and-drop + browse) and the left-panel document list.

---

- [ ] **Task 3.1:** File upload component with drag-and-drop (`@frontend-development`)
  **Priority:** High | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] Drag-and-drop zone accepts PDF files (visual feedback on hover)
  - [ ] File browser fallback button
  - [ ] Customer dropdown populated from `GET /api/v1/customers`
  - [ ] Upload progress indicator
  - [ ] File type validation (PDF only, show error for other types)
  - [ ] Accessible: keyboard-navigable, screen reader announces upload status
  - [ ] Responsive: works on desktop and tablet

  **Implementation Steps:**
  - [ ] Develop: Create `src/components/features/upload/file-upload-zone.tsx` — drag-and-drop with `react-dropzone` or native HTML5 DnD. Create `src/components/features/upload/customer-selector.tsx` — dropdown from API. Create `src/hooks/use-upload-document.ts` — mutation hook calling upload API. Wire into main layout as a dialog/modal accessible from header.
  - [ ] Test: Write `src/components/features/upload/__tests__/file-upload-zone.test.tsx` — test drag events, file type filtering, customer selection, upload trigger.
  - [ ] Verify: `cd frontend && npm test` — all tests pass
  - [ ] Commit: `feat(ui): add file upload zone with drag-and-drop and customer selector`

  **Dependencies:** Tasks 1.5, 2.1

---

- [ ] **Task 3.2:** Customer list API endpoint (`@backend-development`)
  **Priority:** High | **Effort:** S (< 2h)

  **Acceptance Criteria:**
  - [ ] `GET /api/v1/customers` returns list of configured customers with labels
  - [ ] Reads from `config/customers.json`

  **Implementation Steps:**
  - [ ] Develop: Add `backend/app/routers/customers.py` — list endpoint reading from customer config service.
  - [ ] Test: Write `tests/test_customers.py` — verify list returns airbus entry.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(api): add customer list endpoint`

  **Dependencies:** Task 1.4

---

- [ ] **Task 3.3:** Document list sidebar panel (`@frontend-development`)
  **Priority:** High | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] Left sidebar shows list of user's processed documents
  - [ ] Each item shows: filename, customer, status (badge), node count, date
  - [ ] Processing documents show spinner/progress
  - [ ] Failed documents show error indicator
  - [ ] Click selects document and loads nodes in center panel
  - [ ] Active document visually highlighted
  - [ ] Keyboard-navigable (arrow keys, Enter to select)

  **Implementation Steps:**
  - [ ] Develop: Create `src/components/features/documents/document-list.tsx` — fetches from `GET /api/v1/documents`. Create `src/components/features/documents/document-card.tsx` — individual item. Create `src/hooks/use-documents.ts` — SWR/React Query hook with polling for processing status. Wire into app shell sidebar.
  - [ ] Test: Write tests for document list rendering, status badges, selection.
  - [ ] Verify: `cd frontend && npm test` — all tests pass
  - [ ] Commit: `feat(ui): add document list sidebar with status indicators`

  **Dependencies:** Tasks 1.5, 2.3

---

### Sprint 4 — Frontend: Node Viewer with Applicability & Conformity

**Sprint Goal:** Central panel displays extracted nodes in a table with editable Applicability and Conformity dropdown columns.

---

- [ ] **Task 4.1:** Node viewer table component (`@frontend-development`)
  **Priority:** High | **Effort:** L (4–8h)

  **Acceptance Criteria:**
  - [ ] Central panel renders nodes as a data table (order, type, section/req_id, title, description, applicability, conformity)
  - [ ] Title nodes visually distinguished from requirement nodes (background color, indent, or icon)
  - [ ] Table is virtualized for large documents (100+ nodes)
  - [ ] Responsive column layout (description column collapses on narrow screens)
  - [ ] Accessible: proper `<table>` semantics, screen reader support

  **Implementation Steps:**
  - [ ] Develop: Create `src/components/features/nodes/node-table.tsx` — uses shadcn/ui DataTable or TanStack Table. Create `src/components/features/nodes/node-row.tsx`. Create `src/hooks/use-nodes.ts` — fetches from `GET /api/v1/documents/{id}/nodes`. Style title vs requirement rows differently using Tailwind classes.
  - [ ] Test: Write tests for node table rendering, type differentiation, empty state.
  - [ ] Verify: `cd frontend && npm test` — all tests pass
  - [ ] Commit: `feat(ui): add node viewer table with type-differentiated rows`

  **Dependencies:** Tasks 3.3, 2.3

---

- [ ] **Task 4.2:** Applicability and Conformity dropdown columns (`@frontend-development`)
  **Priority:** High | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] Applicability column: dropdown with values `NA`, `A`, `A/M`, `TBC`, `T`
  - [ ] Conformity column: dropdown with values `NA`, `C`, `C TBC`, `PC`, `NC`, `TBC`, `T`
  - [ ] Default for requirement nodes: Applicability=`A`, Conformity=`C`
  - [ ] Default for title nodes: Applicability=`T`, Conformity=`T`
  - [ ] Dropdowns are inline-editable (click to open, select to save)
  - [ ] Optimistic UI: update shown immediately, revert on API failure
  - [ ] Keyboard accessible: Tab into cell, Enter/Space to open dropdown

  **Implementation Steps:**
  - [ ] Develop: Create `src/components/features/nodes/applicability-select.tsx` and `src/components/features/nodes/conformity-select.tsx` — shadcn/ui Select components. Integrate into node table columns. Create `src/hooks/use-update-node.ts` — mutation hook calling `PATCH /api/v1/nodes/{id}`.
  - [ ] Test: Write tests for dropdown rendering, value selection, optimistic update, revert on error.
  - [ ] Verify: `cd frontend && npm test` — all tests pass
  - [ ] Commit: `feat(ui): add Applicability and Conformity inline dropdowns to node table`

  **Dependencies:** Task 4.1

---

- [ ] **Task 4.3:** Node update API endpoint (`@backend-development`)
  **Priority:** High | **Effort:** S (< 2h)

  **Acceptance Criteria:**
  - [ ] `PATCH /api/v1/nodes/{id}` accepts `{ applicability?, conformity? }`
  - [ ] Validates values against allowed enums
  - [ ] Returns updated node
  - [ ] Records `updated_by` and `updated_at`

  **Implementation Steps:**
  - [ ] Develop: Add PATCH route to nodes router. Create `backend/app/schemas/node.py` with update schema (Pydantic with enum validation). Add update method to node repository.
  - [ ] Test: Write `tests/test_node_update.py` — test valid update, invalid enum value rejection, 404 for unknown node.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(api): add node update endpoint for applicability and conformity`

  **Dependencies:** Task 2.3

---

### Sprint 5 — Integration Testing & MVP Polish

**Sprint Goal:** End-to-end flow works, error handling polished, loading states, and documentation.

---

- [ ] **Task 5.1:** End-to-end integration testing (`@backend-development`)
  **Priority:** High | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] Integration test: upload PDF → processing completes → fetch nodes → update node → verify values
  - [ ] Error scenarios: invalid file, processing failure, concurrent access

  **Implementation Steps:**
  - [ ] Develop: Write `tests/test_e2e_flow.py` — full pipeline test using httpx AsyncClient.
  - [ ] Test: Run full test suite.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `test(api): add end-to-end integration tests for document processing flow`

  **Dependencies:** Tasks 2.2, 4.3

---

- [ ] **Task 5.2:** Frontend error handling and loading states (`@frontend-development`)
  **Priority:** High | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] Loading skeletons for document list and node table
  - [ ] Error boundaries with user-friendly messages
  - [ ] Toast notifications for upload success/failure, node update success/failure
  - [ ] Empty states for no documents and no nodes
  - [ ] Processing status polling (auto-refresh when document is processing)

  **Implementation Steps:**
  - [ ] Develop: Add skeleton components, error boundary, toast provider (shadcn/ui Sonner). Add polling logic to `use-documents.ts` for processing documents. Create empty state illustrations.
  - [ ] Test: Write tests for loading, error, and empty states.
  - [ ] Verify: `cd frontend && npm test` — all tests pass
  - [ ] Commit: `feat(ui): add loading skeletons, error handling, and empty states`

  **Dependencies:** Tasks 4.2, 3.3

---

- [ ] **Task 5.3:** Docker containerization (`@backend-development`)
  **Priority:** High | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] `Dockerfile.backend` — multi-stage build for FastAPI backend (includes `reqmap` package)
  - [ ] `Dockerfile.frontend` — multi-stage build for Next.js frontend
  - [ ] `docker-compose.yml` — orchestrates backend + frontend + volume mounts for uploads and SQLite DB
  - [ ] `docker-compose.dev.yml` — development overrides with hot reload for both services
  - [ ] `.dockerignore` files for both services
  - [ ] Single `docker compose up` starts the full application
  - [ ] Uploads directory and SQLite DB persisted via named volumes

  **Implementation Steps:**
  - [ ] Develop: Create `backend/Dockerfile` (Python 3.12, multi-stage: build deps → runtime). Create `frontend/Dockerfile` (Node 20, multi-stage: deps → build → runtime with standalone output). Create `docker-compose.yml` with services `backend` (port 8000) and `frontend` (port 3000), shared network, volumes for `uploads/` and `data/` (SQLite). Create `docker-compose.dev.yml` with bind mounts and hot reload. Add `.dockerignore` for both.
  - [ ] Test: `docker compose build` succeeds. `docker compose up` starts both services. Health check endpoint reachable. Upload → process → view flow works end-to-end in containers.
  - [ ] Verify: `docker compose up --build` — both services start and respond
  - [ ] Commit: `feat(docker): add Dockerfile and docker-compose for full-stack containerization`

  **Dependencies:** Tasks 5.1, 5.2

---

- [ ] **Task 5.4:** Documentation — MVP (`@documentation-writer`)
  **Priority:** Medium | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] `README.md` updated with web app setup instructions (including `docker compose up`)
  - [ ] `model-context.md` created with project architecture, tech stack, conventions
  - [ ] API docs auto-generated from FastAPI OpenAPI schema
  - [ ] `config/customers.json` documented with schema and how to add new customers

  **Implementation Steps:**
  - [ ] Develop: Update `README.md`. Create `model-context.md`. Add docstrings to all API endpoints. Document customer config schema in `config/README.md`.
  - [ ] Verify: All docs render correctly
  - [ ] Commit: `docs: add MVP documentation, model-context, and customer config guide`

  **Dependencies:** Task 5.3

---

## Release 1.1 — Multi-User & Real-Time Collaboration

**Goal:** Multiple users can sign up, log in, process documents, and collaborate on node reviews in real-time with presence awareness and conflict-free concurrent edits.

**Target:** Sprint 6–8 (6 weeks)

---

### Sprint 6 — Authentication & User Management

**Sprint Goal:** JWT-based authentication with user registration, login, and per-user document ownership.

---

- [ ] **Task 6.1:** User table and auth schema (`@database-management`)
  **Priority:** High | **Effort:** S (< 2h)

  **Acceptance Criteria:**
  - [ ] `users` table: `id`, `email`, `hashed_password`, `display_name`, `role` (admin/user), `is_active`, `created_at`
  - [ ] Migration adds FK `uploaded_by` on `documents` and `updated_by` on `nodes` referencing `users.id`

  **Implementation Steps:**
  - [ ] Develop: Add `User` model. Create migration `002_users.py`.
  - [ ] Test: Run migration up/down.
  - [ ] Commit: `feat(db): add users table and auth-related columns`

  **Dependencies:** Task 1.2

---

- [ ] **Task 6.2:** Auth API — register, login, refresh, logout (`@backend-development`)
  **Priority:** High | **Effort:** L (4–8h)

  **Acceptance Criteria:**
  - [ ] `POST /api/v1/auth/register` — create user with hashed password (bcrypt)
  - [ ] `POST /api/v1/auth/login` — issue JWT access token (15min) + refresh token (7d, httpOnly cookie)
  - [ ] `POST /api/v1/auth/refresh` — rotate refresh token
  - [ ] `POST /api/v1/auth/logout` — invalidate refresh token
  - [ ] `GET /api/v1/auth/me` — current user profile
  - [ ] All protected endpoints require valid JWT

  **Implementation Steps:**
  - [ ] Develop: Create `backend/app/routers/auth.py`, `backend/app/services/auth_service.py`, `backend/app/middleware/authenticate.py`. Use `python-jose` for JWT, `passlib[bcrypt]` for password hashing.
  - [ ] Test: Write `tests/test_auth.py` — register, login, token refresh, logout, protected endpoint access.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(auth): implement JWT authentication with register, login, refresh, logout`

  **Dependencies:** Task 6.1

---

- [ ] **Task 6.3:** Frontend auth flow — login, register, protected routes (`@frontend-development`)
  **Priority:** High | **Effort:** L (4–8h)

  **Acceptance Criteria:**
  - [ ] Login and register pages with form validation (Zod + react-hook-form)
  - [ ] Auth context/provider storing user state
  - [ ] Protected route middleware (redirect to login if unauthenticated)
  - [ ] Token refresh handled transparently in API client
  - [ ] User avatar/name in header with logout option

  **Implementation Steps:**
  - [ ] Develop: Create `src/app/(auth)/login/page.tsx`, `src/app/(auth)/register/page.tsx`. Create `src/hooks/use-auth.ts`, `src/lib/auth-provider.tsx`. Add auth interceptor to API client. Update header with user info.
  - [ ] Test: Write tests for login form, registration, protected route redirect.
  - [ ] Verify: `cd frontend && npm test` — all tests pass
  - [ ] Commit: `feat(ui): add authentication flow with login, register, and protected routes`

  **Dependencies:** Tasks 6.2, 1.4

---

- [ ] **Task 6.4:** Document ownership filter (`@backend-development`)
  **Priority:** High | **Effort:** S (< 2h)

  **Acceptance Criteria:**
  - [ ] `GET /api/v1/documents` returns only documents uploaded by the authenticated user (or all for admin)
  - [ ] Upload endpoint sets `uploaded_by` from JWT
  - [ ] Node update sets `updated_by` from JWT

  **Implementation Steps:**
  - [ ] Develop: Add user filtering to document list query. Update upload and node update services to use authenticated user ID.
  - [ ] Test: Write tests verifying ownership filtering.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(api): filter documents by authenticated user ownership`

  **Dependencies:** Tasks 6.2, 2.3

---

### Sprint 7 — Real-Time Collaboration: WebSocket & Presence

**Sprint Goal:** WebSocket-based live updates — when one user changes a node's Applicability/Conformity, all users viewing that document see it instantly. Presence indicators show active users.

---

- [ ] **Task 7.1:** WebSocket server for document channels (`@backend-development`)
  **Priority:** High | **Effort:** L (4–8h)

  **Acceptance Criteria:**
  - [ ] `WS /api/v1/ws/documents/{id}` — authenticated WebSocket per document
  - [ ] Broadcasts node updates to all connected clients on that document
  - [ ] Broadcasts presence events (user joined, user left, user active)
  - [ ] Heartbeat/ping-pong for connection health

  **Implementation Steps:**
  - [ ] Develop: Create `backend/app/routers/ws.py` — WebSocket endpoint with connection manager. Create `backend/app/services/ws_manager.py` — room-based connection tracking, broadcast. Integrate with node update service to emit events post-save.
  - [ ] Test: Write `tests/test_websocket.py` — test connection, message broadcast, presence events.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(ws): add WebSocket server for real-time document collaboration`

  **Dependencies:** Tasks 6.2, 4.3

---

- [ ] **Task 7.2:** Frontend WebSocket client and live updates (`@frontend-development`)
  **Priority:** High | **Effort:** L (4–8h)

  **Acceptance Criteria:**
  - [ ] WebSocket connection established when viewing a document
  - [ ] Node table updates in real-time when another user changes Applicability/Conformity
  - [ ] Visual flash/highlight on changed cells
  - [ ] Reconnection logic with exponential backoff
  - [ ] Connection status indicator in header

  **Implementation Steps:**
  - [ ] Develop: Create `src/hooks/use-document-ws.ts` — WebSocket hook with reconnection. Create `src/lib/ws-client.ts`. Integrate with node table to apply incoming updates. Add cell highlight animation on remote change.
  - [ ] Test: Write tests for WebSocket message handling, state update, reconnection.
  - [ ] Verify: `cd frontend && npm test` — all tests pass
  - [ ] Commit: `feat(ui): add WebSocket client for real-time node updates`

  **Dependencies:** Tasks 7.1, 4.2

---

- [ ] **Task 7.3:** User presence indicators (`@frontend-development`)
  **Priority:** Medium | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] Active user avatars shown in document header when multiple users view the same document
  - [ ] "User X is viewing" tooltip on avatars
  - [ ] User joins/leaves reflected in real-time

  **Implementation Steps:**
  - [ ] Develop: Create `src/components/features/presence/active-users.tsx` — avatar stack from WebSocket presence data. Integrate into node viewer header area.
  - [ ] Test: Write tests for presence rendering, join/leave events.
  - [ ] Verify: `cd frontend && npm test` — all tests pass
  - [ ] Commit: `feat(ui): add user presence indicators for document collaboration`

  **Dependencies:** Task 7.2

---

### Sprint 8 — Role-Based Access & Conflict Resolution

**Sprint Goal:** Role-based UI rendering and server-side authorization. Last-write-wins conflict resolution (CRDT deferred to 2.0 if needed).

---

- [ ] **Task 8.1:** Role-based authorization middleware (`@backend-development`)
  **Priority:** High | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] `authorize(roles)` middleware checks user role from JWT
  - [ ] Admin can see all documents, manage users
  - [ ] Regular users can only see/edit their own documents
  - [ ] Node updates validate document ownership

  **Implementation Steps:**
  - [ ] Develop: Create `backend/app/middleware/authorize.py`. Apply to all protected routes.
  - [ ] Test: Write `tests/test_authorization.py` — test admin vs user access, ownership checks.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(auth): add role-based authorization middleware`

  **Dependencies:** Task 6.2

---

- [ ] **Task 8.2:** Role-based dynamic UI rendering (`@frontend-development`)
  **Priority:** Medium | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] UI adapts based on user role: admin sees all documents, user management link
  - [ ] Non-owner documents are read-only (dropdowns disabled)
  - [ ] Permission-aware component wrapper: `<Authorize role="admin">...</Authorize>`

  **Implementation Steps:**
  - [ ] Develop: Create `src/components/auth/authorize.tsx` — role-based conditional rendering. Update node table dropdowns to be disabled when user lacks edit permission.
  - [ ] Test: Write tests for role-based rendering.
  - [ ] Verify: `cd frontend && npm test` — all tests pass
  - [ ] Commit: `feat(ui): add role-based dynamic rendering for authorization`

  **Dependencies:** Tasks 8.1, 6.3

---

- [ ] **Task 8.3:** Conflict resolution for concurrent edits (`@backend-development`)
  **Priority:** Medium | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] Node update uses optimistic concurrency control (`updated_at` version check)
  - [ ] If two users edit the same node simultaneously, last-write-wins with notification to the overwritten user
  - [ ] WebSocket broadcasts include the updating user's identity so the UI can differentiate local vs remote changes

  **Implementation Steps:**
  - [ ] Develop: Add `version` field to nodes table (or use `updated_at` for optimistic locking). Update PATCH endpoint to check version. Broadcast update events with user info.
  - [ ] Test: Write `tests/test_conflict_resolution.py` — test concurrent update scenarios.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(api): add optimistic concurrency control for node updates`

  **Dependencies:** Tasks 7.1, 4.3

---

## Release 2.0 — Multi-Customer & Polish

**Goal:** Support multiple customer document formats via configurable extractors, add dark/light theme switching, prepare for DOCX support, and meet accessibility standards.

**Target:** Sprint 9–11 (6 weeks)

---

### Sprint 9 — Multi-Customer Extractors

**Sprint Goal:** Make the extraction pipeline customer-aware. Each customer maps to a configurable set of regex patterns and noise filters.

---

- [ ] **Task 9.1:** Configurable node parser factory (`@backend-development`)
  **Priority:** High | **Effort:** L (4–8h)

  **Acceptance Criteria:**
  - [ ] `CustomerNodeParser` class that takes regex config from `customers.json`
  - [ ] Current Airbus patterns extracted from hardcoded `node_parser.py` into config
  - [ ] New customers can be added by editing `customers.json` only (no code changes)
  - [ ] Fallback to generic parser if customer config lacks specific patterns

  **Implementation Steps:**
  - [ ] Develop: Create `backend/app/services/customer_parser.py` — factory that builds `parse_nodes`-compatible functions from JSON config. Refactor processing service to use customer-specific parser. Keep `reqmap/node_parser.py` as the Airbus reference implementation.
  - [ ] Test: Write `tests/test_customer_parser.py` — test with Airbus config, test with a mock second customer config.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(api): implement customer-configurable node parser factory`

  **Dependencies:** Tasks 1.3, 1.4

---

- [ ] **Task 9.2:** Admin UI for customer management (`@frontend-development`)
  **Priority:** Medium | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] Admin page to view configured customers
  - [ ] Shows customer name, label, configured patterns
  - [ ] (Read-only for MVP — editing config via UI deferred)

  **Implementation Steps:**
  - [ ] Develop: Create `src/app/(protected)/admin/customers/page.tsx`. Display customer config data in a table.
  - [ ] Test: Write component tests.
  - [ ] Verify: `cd frontend && npm test` — all tests pass
  - [ ] Commit: `feat(ui): add admin customer configuration viewer`

  **Dependencies:** Tasks 8.2, 3.2

---

### Sprint 10 — Theme Switching & Accessibility

**Sprint Goal:** Seamless dark/light mode, WCAG 2.1 AA compliance audit, keyboard navigation everywhere.

---

- [ ] **Task 10.1:** Dark/light theme with centralized tokens (`@frontend-development`)
  **Priority:** Medium | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] Theme toggle in header (sun/moon icon)
  - [ ] Persisted in localStorage and respects `prefers-color-scheme`
  - [ ] All components use CSS custom properties — zero hardcoded colors
  - [ ] Smooth transition between themes (no flash of wrong theme on load)

  **Implementation Steps:**
  - [ ] Develop: Finalize `globals.css` with full dark/light token sets. Update all custom components to use tokens only. Add `next-themes` integration. Test every page in both themes.
  - [ ] Test: Visual regression testing or manual audit of all pages in both themes.
  - [ ] Verify: `cd frontend && npm run build` — builds with no errors
  - [ ] Commit: `feat(ui): implement dark/light theme switching with centralized design tokens`

  **Dependencies:** Task 1.5

---

- [ ] **Task 10.2:** Accessibility audit and fixes (`@frontend-development`)
  **Priority:** Medium | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] All interactive elements keyboard-navigable with visible focus indicators
  - [ ] Color contrast meets WCAG 2.1 AA (4.5:1 for text, 3:1 for large text)
  - [ ] Semantic HTML throughout (`<nav>`, `<main>`, `<table>`, `<button>`)
  - [ ] ARIA labels on icon-only buttons, dropdowns, and status indicators
  - [ ] Screen reader tested (NVDA or VoiceOver) on key flows: upload, browse documents, edit node

  **Implementation Steps:**
  - [ ] Develop: Run axe-core audit. Fix all critical and serious issues. Add `aria-label` props. Ensure focus management on modal open/close. Add skip navigation link.
  - [ ] Test: Write accessibility tests with `@testing-library/jest-dom` `toBeAccessible` or axe integration.
  - [ ] Verify: `cd frontend && npm test` — all tests pass
  - [ ] Commit: `fix(a11y): resolve accessibility issues for WCAG 2.1 AA compliance`

  **Dependencies:** Tasks 4.2, 3.3

---

### Sprint 11 — DOCX Preparation & Final Polish

**Sprint Goal:** Prepare the architecture for DOCX/DOC support (not full implementation), finalize i18n readiness, and polish the UX.

---

- [ ] **Task 11.1:** DOCX upload acceptance and placeholder processing (`@backend-development`)
  **Priority:** Low | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] Upload endpoint accepts `.docx` and `.doc` in addition to `.pdf`
  - [ ] Non-PDF files stored with `status=unsupported` and user-friendly message
  - [ ] Architecture ready: processing service has a format dispatcher (PDF → reqmap, DOCX → future)

  **Implementation Steps:**
  - [ ] Develop: Update file validation to accept docx/doc MIME types. Add format dispatcher in processing service. Return `status=unsupported` with message for non-PDF formats.
  - [ ] Test: Write tests for docx upload acceptance, status handling.
  - [ ] Verify: `cd backend && pytest` — all tests pass
  - [ ] Commit: `feat(api): accept DOCX/DOC uploads with format dispatcher architecture`

  **Dependencies:** Task 2.1

---

- [ ] **Task 11.2:** i18n preparation (`@frontend-development`)
  **Priority:** Low | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] All user-facing strings extracted to translation files (using `next-intl` or `react-i18next`)
  - [ ] English locale complete
  - [ ] RTL layout support via logical CSS properties
  - [ ] Locale switcher component (English only for now, but framework ready)

  **Implementation Steps:**
  - [ ] Develop: Install and configure i18n library. Extract all hardcoded strings to `messages/en.json`. Replace all strings with translation keys. Add locale switcher in header.
  - [ ] Test: Verify all pages render correctly with translation keys.
  - [ ] Verify: `cd frontend && npm run build` — builds with no errors
  - [ ] Commit: `feat(i18n): extract all strings for internationalization readiness`

  **Dependencies:** Task 1.5

---

- [ ] **Task 11.3:** Final documentation and model-context (`@documentation-writer`)
  **Priority:** Medium | **Effort:** M (2–4h)

  **Acceptance Criteria:**
  - [ ] `model-context.md` comprehensive and up-to-date
  - [ ] API documentation complete (all endpoints documented)
  - [ ] Customer config guide with examples for adding new customers
  - [ ] User manual: upload → process → review → export flow

  **Implementation Steps:**
  - [ ] Develop: Finalize all documentation files.
  - [ ] Verify: Review all docs for accuracy.
  - [ ] Commit: `docs: finalize project documentation and user guide`

  **Dependencies:** Tasks 5.3

---

## Architecture Summary

```
ReqMap/
├── reqmap/                  # Python extraction tools (refactored: configurable patterns)
├── backend/                 # new FastAPI backend
│   ├── app/
│   │   ├── main.py          # FastAPI app entry
│   │   ├── config.py        # Pydantic Settings (env vars)
│   │   ├── database.py      # SQLAlchemy async engine + session
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── routers/         # API route handlers
│   │   ├── services/        # Business logic
│   │   ├── repositories/    # Data access layer
│   │   ├── schemas/         # Pydantic request/response models
│   │   └── middleware/       # Auth, validation, error handling
│   ├── alembic/             # Database migrations
│   ├── tests/               # Backend tests (pytest)
│   └── pyproject.toml       # Python dependencies
├── frontend/                # new Next.js frontend
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   ├── components/
│   │   │   ├── ui/          # shadcn/ui primitives
│   │   │   ├── features/    # Feature-specific components
│   │   │   ├── layout/      # App shell, header, sidebar
│   │   │   └── auth/        # Auth-related components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── lib/             # API client, utils, constants
│   │   └── styles/          # Global CSS with design tokens
│   ├── messages/            # i18n translation files
│   └── package.json
├── config/
│   └── customers.json       # Customer → extractor mapping
├── uploads/                 # Uploaded files (gitignored)
├── docker-compose.yml       # Production compose
├── docker-compose.dev.yml   # Dev compose with hot reload
├── model-context.md         # AI persistent memory
└── README.md
```

## Risk Factors

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large PDFs slow to process | Processing timeout | Background task with progress reporting, configurable timeout |
| Airbus-specific regex doesn't generalize | New customers need code changes | Config-driven parser factory, fallback generic parser |
| WebSocket scaling | Memory pressure with many connections | Room-based connection management, connection limits |
| SQLite concurrency limits | Write contention in multi-user | Plan PostgreSQL migration path; SQLite sufficient for small teams |
| Docker image size | Large images with OCR dependencies | Multi-stage builds, shared base layer for Python deps |

---

## Key Numbers

- **3 releases**, **11 sprints** (~22 weeks / 5.5 months)
- **~33 tasks** with full develop → test → commit cycles
- **Estimated effort:** ~160–210 hours total
