# Software Requirements Specification — ReqMap

**Document ID:** HEM-REQMAP-SRS-001
**Project:** ReqMap
**Organisation:** HEMERIA
**Status:** Draft
**Date:** 2026-04-22

---

## Revision History

| Revision | Date       | Author      | Summary of Changes                             |
|----------|------------|-------------|------------------------------------------------|
| 0.1      | 2026-04-10 | L. Carcagno | Initial skeleton.                              |
| 0.2      | 2026-04-15 | L. Carcagno | Added functional requirements for extraction.  |
| 0.3      | 2026-04-18 | L. Carcagno | Added frontend and persistence requirements.   |
| 1.0      | 2026-04-22 | L. Carcagno | First baseline. Aligned with v1.0 MVP release. |

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the functional and non-functional requirements for **ReqMap**, an internal HEMERIA tooling system that extracts, structures, and supports the review of requirements contained in customer specification documents delivered as PDF files.

The document is intended for:

- **Development engineers** implementing and maintaining the system.
- **Verification and validation engineers** designing acceptance test campaigns.
- **Project managers and product owners** tracking scope and baseline evolution.
- **Customer stakeholders** requiring a contractual reference of delivered functionality.

### 1.2 Scope

ReqMap shall turn requirement-bearing PDF documents into an ordered list of reviewable, structured nodes (*title* and *requirement*) persisted in a database, and shall expose these nodes through a web user interface supporting inline review, annotation of applicability and conformity, and document lifecycle management.

In scope for baseline **V0 (v1.0 MVP)**:

- PDF ingestion, extraction, cleaning, and node parsing.
- Customer-configurable extraction patterns.
- Persistence to a local relational database.
- REST API for document and node operations.
- Web-based review user interface.

Out of scope for V0 but addressed in future baselines (V1, V2):

- User authentication and authorisation.
- Real-time collaborative editing.
- Non-PDF document formats.
- Export to external formats (CSV, Excel).
- Audit trail.

### 1.3 Definitions, Acronyms and Abbreviations

| Term / Acronym | Definition                                                                                         |
|----------------|----------------------------------------------------------------------------------------------------|
| API            | Application Programming Interface.                                                                 |
| Applicability  | Enumerated qualifier expressing to what extent a requirement applies to the project.               |
| Conformity     | Enumerated qualifier expressing the degree to which the project complies with a requirement.       |
| Customer       | Issuer of a specification document, identified by a named extractor profile.                       |
| MVP            | Minimum Viable Product.                                                                            |
| Node           | Atomic unit produced by the extraction pipeline — either a *title* or a *requirement*.             |
| OCR            | Optical Character Recognition.                                                                     |
| ORM            | Object-Relational Mapper.                                                                          |
| PDF            | Portable Document Format (ISO 32000).                                                              |
| REST           | Representational State Transfer.                                                                   |
| SRS            | Software Requirements Specification.                                                               |
| TBC            | To Be Confirmed.                                                                                   |
| UI             | User Interface.                                                                                    |

### 1.4 References

- IEEE Std 830-1998 — Recommended Practice for Software Requirements Specifications.
- ISO/IEC/IEEE 29148:2018 — Systems and software engineering — Life cycle processes — Requirements engineering.
- Project repository `CLAUDE.md` — Architectural overview.
- Project repository `model-context.md` — Roadmap.

### 1.5 Document Overview

Section 2 provides a system-level overview. Section 3 enumerates functional requirements grouped by functional domain. Section 4 lists non-functional requirements. Section 5 describes external interfaces. Section 6 captures future-baseline requirements. Appendices contain a traceability matrix and a glossary.

---

## 2. Overall Description

### 2.1 Product Perspective

ReqMap is a standalone three-layer software system. Each layer is separately deployable but typically runs co-located behind a single Docker Compose orchestration:

1. **`reqmap` library** — A Python library responsible for PDF-to-markdown extraction and node parsing. Usable both programmatically and as a CLI.
2. **Backend service** — A FastAPI application that wraps the library, manages persistence in SQLite, and exposes a REST API.
3. **Frontend application** — A Next.js single-page application providing the document upload, dashboard, and review interface.

### 2.2 Product Functions

Primary functions include:

- Upload a PDF and select an extractor profile.
- Extract the PDF content to clean markdown with optional OCR on inline images.
- Parse the markdown into an ordered list of typed nodes.
- Persist documents and nodes to a relational store.
- Browse, inspect and edit nodes through a web UI.
- Track applicability and conformity of each requirement.
- Delete documents and their dependent data.

### 2.3 User Classes and Characteristics

| User Class      | Description                                                            | Technical Proficiency |
|-----------------|------------------------------------------------------------------------|------------------------|
| Review Engineer | Principal user. Uploads documents and reviews extracted requirements.  | Intermediate.          |
| Administrator   | Maintains customer profiles and deploys the system.                    | Advanced.              |
| Integrator      | Uses the `reqmap` library directly in external pipelines or scripts.   | Advanced (Python).     |

### 2.4 Operating Environment

- Backend: Python 3.12 or later, Linux or Windows, Docker 24+.
- Frontend: Node.js 20 or later, evergreen browsers (Chrome, Firefox, Edge — two latest major versions).
- Database: SQLite 3.35+ (bundled).

### 2.5 Design and Implementation Constraints

- The backend shall be implemented in Python using the FastAPI framework.
- The ORM shall be SQLAlchemy 2.x in asynchronous mode.
- Request and response schemas shall be Pydantic v2 models.
- The frontend shall be implemented in TypeScript using Next.js 15 and React 19.
- Server-state management on the frontend shall use TanStack Query.
- The system shall be deployable via Docker Compose.

### 2.6 Assumptions and Dependencies

- Input PDFs are textual or contain images recoverable by OCR.
- Host machines have sufficient disk space for uploaded PDFs and the SQLite database.
- Network access is available at build time to fetch package dependencies.

---

## 3. Functional Requirements

### 3.1 Document Ingestion

This section defines requirements governing how PDF documents enter the system: acceptance criteria, storage of uploaded files, and association with a customer extractor profile.

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 1                                                                                                       |
| **Title**         | PDF upload endpoint                                                                                     |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 28                                                                                                      |
| **Description**   | The system shall expose an HTTP POST endpoint accepting a PDF file and a customer identifier as multipart form data. |
| **Note**          | See REST API section for endpoint path conventions.                                                     |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 2                                                                                                       |
| **Title**         | File type validation                                                                                    |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 1                                                                                                       |
| **Description**   | The system shall reject any uploaded file whose MIME type is not `application/pdf` with an HTTP 415 response. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 3                                                                                                       |
| **Title**         | Maximum file size                                                                                       |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 1                                                                                                       |
| **Description**   | The system shall reject uploads whose size exceeds 100 MB with an HTTP 413 response.                    |
| **Note**          | Threshold is configurable via environment variable `MAX_UPLOAD_SIZE_MB`.                                |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 4                                                                                                       |
| **Title**         | Persistent file storage                                                                                 |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Inspection                                                                                              |
| **Linked Req**    | 1                                                                                                       |
| **Description**   | The system shall store uploaded PDF files in a dedicated directory on persistent storage outside the application bundle. |
| **Note**          | Directory defaults to `./uploads/` and is configurable.                                                 |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 5                                                                                                       |
| **Title**         | Customer profile binding                                                                                |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 1, 18                                                                                                   |
| **Description**   | The system shall associate each uploaded document with a valid customer identifier supplied at upload time and shall reject unknown identifiers with an HTTP 400 response. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 6                                                                                                       |
| **Title**         | Asynchronous processing                                                                                 |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 1                                                                                                       |
| **Description**   | The system shall return an HTTP 202 response with a document identifier immediately after validating an upload, and shall perform extraction and parsing in a background task. |
| **Note**          | Status is polled through requirement 31.                                                                |

### 3.2 PDF Extraction and OCR

Extraction converts a PDF into a markdown representation that preserves logical structure (headings, paragraphs, lists, tables) while stripping layout artefacts.

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 7                                                                                                       |
| **Title**         | Markdown extraction                                                                                     |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 6                                                                                                       |
| **Description**   | The system shall extract the textual content of a PDF into markdown preserving heading hierarchy, paragraph breaks, ordered and unordered lists. |
| **Note**          | Implemented via `pymupdf4llm`.                                                                          |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 8                                                                                                       |
| **Title**         | Inline image OCR                                                                                        |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 7                                                                                                       |
| **Description**   | The system shall perform optical character recognition on each inline raster image embedded in the PDF and shall insert the recognised text in-place within the extracted markdown. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 9                                                                                                       |
| **Title**         | OCR opt-out                                                                                             |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 8                                                                                                       |
| **Description**   | The system shall provide a `--no-ocr` CLI flag and an equivalent API parameter that, when set, disables inline-image OCR. |
| **Note**          | Improves extraction speed when documents are known to be text-only.                                     |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 10                                                                                                      |
| **Title**         | Header and footer removal                                                                               |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 7                                                                                                       |
| **Description**   | The system shall detect and remove repeating page headers and footers from the extracted markdown.      |
| **Note**          | Detection based on recurrence across pages.                                                             |

### 3.3 Markdown Cleaning

The cleaning stage eliminates non-semantic noise (page numbers, boilerplate, repeated separators) to produce a markdown stream suited to downstream parsing.

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 11                                                                                                      |
| **Title**         | Noise pattern stripping                                                                                 |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 21                                                                                                      |
| **Description**   | The system shall remove every line of the extracted markdown that matches any regular expression listed under the active customer's `noise_patterns`. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 12                                                                                                      |
| **Title**         | Cleaning opt-out                                                                                        |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 11                                                                                                      |
| **Description**   | The system shall provide a `--no-clean` CLI flag that, when set, skips the markdown cleaning stage and passes the raw extracted markdown to the parser. |
| **Note**          | Useful for troubleshooting extractor regressions.                                                       |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 13                                                                                                      |
| **Title**         | Requirement identifier preservation                                                                     |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 11                                                                                                      |
| **Description**   | The cleaning stage shall never remove a line that contains a match of the active customer's `req_id_pattern`. |
| **Note**          | Safety guard against over-aggressive noise filters.                                                     |

### 3.4 Node Parsing

Node parsing walks the cleaned markdown and emits an ordered list of structured nodes.

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 14                                                                                                      |
| **Title**         | Title node emission                                                                                     |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 20                                                                                                      |
| **Description**   | For each line matching the active customer's `title_pattern`, the system shall emit a node whose `type` is `"title"`. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 15                                                                                                      |
| **Title**         | Requirement node emission                                                                               |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 19                                                                                                      |
| **Description**   | For each line matching the active customer's `req_id_pattern`, the system shall emit a node whose `type` is `"requirement"` and whose `req_id` is set to the matched identifier. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 16                                                                                                      |
| **Title**         | Sequential ordering                                                                                     |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 14, 15                                                                                                  |
| **Description**   | The system shall assign to each emitted node an `order` attribute containing its zero-based index in document reading order. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 17                                                                                                      |
| **Title**         | Section context propagation                                                                             |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 14, 15                                                                                                  |
| **Description**   | Each requirement node shall carry a `section` attribute set to the title text of its nearest preceding title node. |
| **Note**          | Empty string when no preceding title exists.                                                            |

### 3.5 Customer Configuration

Customer profiles externalise all document-specific extraction logic into declarative configuration.

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 18                                                                                                      |
| **Title**         | Customer configuration file                                                                             |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Inspection                                                                                              |
| **Linked Req**    | None                                                                                                    |
| **Description**   | The system shall load customer profiles at startup from a JSON file located at `config/customers.json`. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 19                                                                                                      |
| **Title**         | Custom requirement identifier pattern                                                                   |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 18                                                                                                      |
| **Description**   | Each customer profile shall support a `req_id_pattern` field containing a valid Python regular expression. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 20                                                                                                      |
| **Title**         | Custom title pattern                                                                                    |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 18                                                                                                      |
| **Description**   | Each customer profile shall support a `title_pattern` field containing a valid Python regular expression. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 21                                                                                                      |
| **Title**         | Custom noise patterns                                                                                   |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 18                                                                                                      |
| **Description**   | Each customer profile shall support a `noise_patterns` field containing an array of valid Python regular expressions. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 22                                                                                                      |
| **Title**         | Default Airbus profile                                                                                  |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Inspection                                                                                              |
| **Linked Req**    | 18                                                                                                      |
| **Description**   | The system shall ship with a default customer profile identified as `airbus` tuned for Airbus specification formats. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 23                                                                                                      |
| **Title**         | Customer enumeration endpoint                                                                           |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 18                                                                                                      |
| **Description**   | The system shall expose an HTTP GET endpoint returning the list of currently configured customer profiles including their identifier and display label. |
| **Note**          | Used by the frontend upload dropdown.                                                                   |

### 3.6 Persistence and Data Management

The persistence layer stores documents, nodes and their editable attributes.

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 24                                                                                                      |
| **Title**         | Document persistence                                                                                    |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 6                                                                                                       |
| **Description**   | The system shall persist each uploaded document as a single row in a `documents` table including its identifier, original filename, customer identifier, upload timestamp and processing status. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 25                                                                                                      |
| **Title**         | Node persistence                                                                                        |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 24                                                                                                      |
| **Description**   | The system shall persist each parsed node as a row in a `nodes` table with a foreign key reference to its parent document. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 26                                                                                                      |
| **Title**         | Cascading deletion                                                                                      |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 25, 32                                                                                                  |
| **Description**   | Deleting a document shall cascade to the deletion of all its associated nodes and the deletion of the stored PDF file. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 27                                                                                                      |
| **Title**         | Idempotent schema migration                                                                             |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 24                                                                                                      |
| **Description**   | The system shall apply additive schema migrations at startup in an idempotent manner such that starting the service against an up-to-date schema results in no error and no change. |
| **Note**          | Implementation uses try/except around `ALTER TABLE ADD COLUMN` statements.                              |

### 3.7 REST API

The backend exposes a versioned REST API consumed by the frontend and usable by external tooling.

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 28                                                                                                      |
| **Title**         | API versioning                                                                                          |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Inspection                                                                                              |
| **Linked Req**    | None                                                                                                    |
| **Description**   | All REST endpoints shall be served under a path prefix of the form `/api/v{major}/` where `{major}` is the API major version. |
| **Note**          | Baseline V0 uses `/api/v1/`.                                                                            |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 29                                                                                                      |
| **Title**         | Document retrieval endpoint                                                                             |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 24                                                                                                      |
| **Description**   | The system shall expose an HTTP GET endpoint returning the full document metadata and its ordered list of nodes for a given document identifier. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 30                                                                                                      |
| **Title**         | Document listing endpoint                                                                               |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 24                                                                                                      |
| **Description**   | The system shall expose an HTTP GET endpoint returning the list of all documents including their identifier, title, customer identifier, status and summary conformity statistics. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 31                                                                                                      |
| **Title**         | Processing status endpoint                                                                              |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 6                                                                                                       |
| **Description**   | The system shall expose an HTTP GET endpoint returning the current processing status of a given document, with values drawn from the set `{pending, processing, completed, failed}`. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 32                                                                                                      |
| **Title**         | Document deletion endpoint                                                                              |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 26                                                                                                      |
| **Description**   | The system shall expose an HTTP DELETE endpoint removing a document, its nodes and its stored PDF file, returning HTTP 204 on success. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 33                                                                                                      |
| **Title**         | Node update endpoint                                                                                    |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 25                                                                                                      |
| **Description**   | The system shall expose an HTTP PATCH endpoint allowing modification of a node's `applicability`, `conformity`, and textual remarks fields. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 34                                                                                                      |
| **Title**         | OpenAPI documentation                                                                                   |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Inspection                                                                                              |
| **Linked Req**    | 28                                                                                                      |
| **Description**   | The system shall publish an interactive OpenAPI 3.1 documentation page at `/api/docs` describing every REST endpoint, its parameters and its response schemas. |
| **Note**          |                                                                                                         |

### 3.8 Frontend Upload and Dashboard

This section addresses the user-facing flows for uploading documents and navigating their processing status.

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 35                                                                                                      |
| **Title**         | Upload form                                                                                             |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Demonstration                                                                                           |
| **Linked Req**    | 1                                                                                                       |
| **Description**   | The frontend shall present a form allowing the user to select a local PDF file and a customer profile before submission. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 36                                                                                                      |
| **Title**         | Customer dropdown population                                                                            |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Demonstration                                                                                           |
| **Linked Req**    | 23, 35                                                                                                  |
| **Description**   | The frontend shall populate the customer selection dropdown dynamically from the customer enumeration endpoint. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 37                                                                                                      |
| **Title**         | Processing progress modal                                                                               |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Demonstration                                                                                           |
| **Linked Req**    | 31                                                                                                      |
| **Description**   | Upon upload submission the frontend shall display a modal polling the processing status endpoint at most once per 2 seconds until the status reaches `completed` or `failed`. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 38                                                                                                      |
| **Title**         | Dashboard document listing                                                                              |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Demonstration                                                                                           |
| **Linked Req**    | 30                                                                                                      |
| **Description**   | The frontend shall display a dashboard listing every processed document with its title, customer, upload date and overall conformity summary. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 39                                                                                                      |
| **Title**         | Dashboard conformity chart                                                                              |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Demonstration                                                                                           |
| **Linked Req**    | 38                                                                                                      |
| **Description**   | The dashboard shall render, for each document, a pie chart showing the distribution of conformity values across its requirement nodes. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 40                                                                                                      |
| **Title**         | Dashboard deletion action                                                                               |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Demonstration                                                                                           |
| **Linked Req**    | 32                                                                                                      |
| **Description**   | The dashboard shall provide a deletion control requiring explicit user confirmation before calling the deletion endpoint. |
| **Note**          |                                                                                                         |

### 3.9 Node Review and Editing

This section covers the detailed node review experience used by review engineers.

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 41                                                                                                      |
| **Title**         | Ordered node table                                                                                      |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Demonstration                                                                                           |
| **Linked Req**    | 16, 29                                                                                                  |
| **Description**   | The review screen shall display nodes in ascending `order` in a tabular layout.                         |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 42                                                                                                      |
| **Title**         | Markdown description rendering                                                                          |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Demonstration                                                                                           |
| **Linked Req**    | 41                                                                                                      |
| **Description**   | The review screen shall render each node's `description` as sanitised HTML derived from its markdown source, supporting paragraphs, lists, bold, italic, inline code and tables. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 43                                                                                                      |
| **Title**         | Inline applicability editing                                                                            |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Demonstration                                                                                           |
| **Linked Req**    | 33, 45                                                                                                  |
| **Description**   | The review screen shall allow the user to change a node's applicability through a select control constrained to the authorised enumerated values. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 44                                                                                                      |
| **Title**         | Inline conformity editing                                                                               |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Demonstration                                                                                           |
| **Linked Req**    | 33, 46                                                                                                  |
| **Description**   | The review screen shall allow the user to change a node's conformity through a select control constrained to the authorised enumerated values. |
| **Note**          |                                                                                                         |

### 3.10 Applicability and Conformity Enumerations

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 45                                                                                                      |
| **Title**         | Applicability values                                                                                    |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | None                                                                                                    |
| **Description**   | The system shall constrain the `applicability` field of any node to the set `{NA, A, A/M, TBC, T}`.     |
| **Note**          | Constraint enforced both at ORM layer and UI control.                                                   |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 46                                                                                                      |
| **Title**         | Conformity values                                                                                       |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | None                                                                                                    |
| **Description**   | The system shall constrain the `conformity` field of any node to the set `{NA, C, C TBC, PC, NC, TBC, T}`. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 47                                                                                                      |
| **Title**         | Default values per node type                                                                            |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 45, 46                                                                                                  |
| **Description**   | Newly parsed requirement nodes shall default to applicability `A` and conformity `C`, and newly parsed title nodes shall default to applicability `T` and conformity `T`. |
| **Note**          |                                                                                                         |

---

## 4. Non-Functional Requirements

### 4.1 Performance

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 48                                                                                                      |
| **Title**         | Extraction throughput                                                                                   |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 7                                                                                                       |
| **Description**   | The system shall complete extraction and parsing of a 100-page text-only PDF within 60 seconds on a reference environment of 4 vCPU / 8 GB RAM. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 49                                                                                                      |
| **Title**         | API responsiveness                                                                                      |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 28                                                                                                      |
| **Description**   | Non-extraction REST endpoints shall return a response within 500 milliseconds at the 95th percentile under a load of 10 concurrent clients. |
| **Note**          |                                                                                                         |

### 4.2 Reliability and Robustness

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 50                                                                                                      |
| **Title**         | Extraction failure containment                                                                          |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 6, 31                                                                                                   |
| **Description**   | A failure during background extraction shall leave the corresponding document's status as `failed` without terminating or degrading the backend service. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 51                                                                                                      |
| **Title**         | Session isolation for background tasks                                                                  |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Inspection                                                                                              |
| **Linked Req**    | 6                                                                                                       |
| **Description**   | Background processing tasks shall use database sessions distinct from any request-scoped session.       |
| **Note**          | Enforced by opening fresh `AsyncSessionLocal` instances inside the background worker.                   |

### 4.3 Security

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 52                                                                                                      |
| **Title**         | Input validation                                                                                        |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 28                                                                                                      |
| **Description**   | Every REST endpoint shall validate its inputs against a Pydantic v2 schema and shall return HTTP 422 on validation failure. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 53                                                                                                      |
| **Title**         | Markdown rendering sanitisation                                                                         |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 42                                                                                                      |
| **Description**   | The frontend shall sanitise rendered markdown to strip any script tags and inline event handlers.        |
| **Note**          | Mitigates XSS from adversarial PDF content.                                                             |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 54                                                                                                      |
| **Title**         | Secret management                                                                                       |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Inspection                                                                                              |
| **Linked Req**    | None                                                                                                    |
| **Description**   | Secrets shall be supplied to the application exclusively through environment variables and shall never appear in version control. |
| **Note**          | `.env` files are git-ignored; `.env.example` is provided.                                               |

### 4.4 Usability

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 55                                                                                                      |
| **Title**         | Light and dark themes                                                                                   |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Demonstration                                                                                           |
| **Linked Req**    | None                                                                                                    |
| **Description**   | The frontend shall provide both a light and a dark visual theme switchable without page reload.         |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 56                                                                                                      |
| **Title**         | Responsive layout                                                                                       |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Demonstration                                                                                           |
| **Linked Req**    | None                                                                                                    |
| **Description**   | The frontend shall render correctly at viewport widths of 1280 pixels and above without horizontal scrolling. |
| **Note**          |                                                                                                         |

### 4.5 Maintainability

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 57                                                                                                      |
| **Title**         | Layered backend architecture                                                                            |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Inspection                                                                                              |
| **Linked Req**    | None                                                                                                    |
| **Description**   | Backend code shall be organised in four layers — routers, services, repositories, models — with dependencies flowing in one direction only from the outermost to the innermost layer. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 58                                                                                                      |
| **Title**         | Type hints coverage                                                                                     |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Analysis                                                                                                |
| **Linked Req**    | None                                                                                                    |
| **Description**   | Every public function or method in Python source shall carry complete type annotations on its parameters and return value. |
| **Note**          | Verified via static type checker configured in CI.                                                      |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 59                                                                                                      |
| **Title**         | Automated test coverage                                                                                 |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Analysis                                                                                                |
| **Linked Req**    | None                                                                                                    |
| **Description**   | Backend unit and integration test coverage, measured by statement coverage, shall be at least 70% for the `reqmap` library and 60% for the backend service. |
| **Note**          |                                                                                                         |

### 4.6 Portability and Deployment

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 60                                                                                                      |
| **Title**         | Docker Compose deployment                                                                               |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Demonstration                                                                                           |
| **Linked Req**    | None                                                                                                    |
| **Description**   | The full system shall be deployable on any Docker 24+ host through a single `docker compose up --build` command. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 61                                                                                                      |
| **Title**         | Platform support                                                                                        |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V0                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | None                                                                                                    |
| **Description**   | The backend and `reqmap` library shall run unmodified on Linux and Windows hosts running Python 3.12 or later. |
| **Note**          |                                                                                                         |

---

## 5. External Interfaces

### 5.1 Hardware Interfaces

ReqMap does not interact with specialised hardware. CPU and RAM resources are consumed as described in section 4.1.

### 5.2 Software Interfaces

| External Component | Purpose                                         | Protocol / API        |
|--------------------|-------------------------------------------------|-----------------------|
| `pymupdf4llm`      | PDF-to-markdown extraction                      | Python import         |
| OCR engine         | Optical recognition of inline raster images     | Python import         |
| SQLite             | Persistent storage                              | SQL via SQLAlchemy    |
| Browser            | User-facing interface                           | HTTP / HTML5          |

### 5.3 Communication Interfaces

- HTTP/1.1 and HTTP/2 over TLS (recommended in production deployments).
- JSON request and response payloads over REST.
- `multipart/form-data` for PDF upload.

---

## 6. Future Baselines

### 6.1 V1 — Authentication and Collaboration

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 62                                                                                                      |
| **Title**         | JWT authentication                                                                                      |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V1                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | None                                                                                                    |
| **Description**   | The backend shall authenticate each incoming REST request through a bearer JSON Web Token signed with a configurable secret key. |
| **Note**          | Configuration stubs already present in `backend/app/config.py`.                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 63                                                                                                      |
| **Title**         | Real-time collaborative editing                                                                         |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V1                                                                                                      |
| **Verified By**   | Demonstration                                                                                           |
| **Linked Req**    | 33                                                                                                      |
| **Description**   | The system shall broadcast node-level updates over WebSocket to every connected client viewing the same document. |
| **Note**          |                                                                                                         |

### 6.2 V2 — Format Extension and Exports

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 64                                                                                                      |
| **Title**         | DOCX ingestion                                                                                          |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V2                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 1                                                                                                       |
| **Description**   | The system shall accept Microsoft Word `.docx` files through the same ingestion pipeline as PDF files.   |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 65                                                                                                      |
| **Title**         | CSV export                                                                                              |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V2                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 29                                                                                                      |
| **Description**   | The system shall expose an HTTP GET endpoint returning the full node list of a document as a UTF-8 encoded CSV attachment. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 66                                                                                                      |
| **Title**         | Excel export                                                                                            |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V2                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 65                                                                                                      |
| **Description**   | The system shall expose an HTTP GET endpoint returning the full node list of a document as an XLSX attachment with one sheet per parent section. |
| **Note**          |                                                                                                         |

| Field             | Value                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**| 67                                                                                                      |
| **Title**         | Audit trail                                                                                             |
| **Version**       | 1                                                                                                       |
| **Applicable To** | V2                                                                                                      |
| **Verified By**   | Test                                                                                                    |
| **Linked Req**    | 33                                                                                                      |
| **Description**   | Every modification applied to a node shall be recorded in an append-only audit log capturing the timestamp, acting user identifier, old value and new value of each changed field. |
| **Note**          |                                                                                                         |

---

## 7. Requirements Traceability Matrix

The matrix below traces each requirement back to its originating functional domain and forward to the verification activity.

| Req ID | Title                                       | Domain                      | Baseline | Verified By     | Linked     |
|--------|---------------------------------------------|------------------------------|----------|-----------------|------------|
| 1      | PDF upload endpoint                         | Ingestion                    | V0       | Test            | 28         |
| 2      | File type validation                        | Ingestion                    | V0       | Test            | 1          |
| 3      | Maximum file size                           | Ingestion                    | V0       | Test            | 1          |
| 4      | Persistent file storage                     | Ingestion                    | V0       | Inspection      | 1          |
| 5      | Customer profile binding                    | Ingestion                    | V0       | Test            | 1, 18      |
| 6      | Asynchronous processing                     | Ingestion                    | V0       | Test            | 1          |
| 7      | Markdown extraction                         | Extraction / OCR             | V0       | Test            | 6          |
| 8      | Inline image OCR                            | Extraction / OCR             | V0       | Test            | 7          |
| 9      | OCR opt-out                                 | Extraction / OCR             | V0       | Test            | 8          |
| 10     | Header and footer removal                   | Extraction / OCR             | V0       | Test            | 7          |
| 11     | Noise pattern stripping                     | Cleaning                     | V0       | Test            | 21         |
| 12     | Cleaning opt-out                            | Cleaning                     | V0       | Test            | 11         |
| 13     | Requirement identifier preservation         | Cleaning                     | V0       | Test            | 11         |
| 14     | Title node emission                         | Parsing                      | V0       | Test            | 20         |
| 15     | Requirement node emission                   | Parsing                      | V0       | Test            | 19         |
| 16     | Sequential ordering                         | Parsing                      | V0       | Test            | 14, 15     |
| 17     | Section context propagation                 | Parsing                      | V0       | Test            | 14, 15     |
| 18     | Customer configuration file                 | Customer Configuration       | V0       | Inspection      | —          |
| 19     | Custom requirement identifier pattern       | Customer Configuration       | V0       | Test            | 18         |
| 20     | Custom title pattern                        | Customer Configuration       | V0       | Test            | 18         |
| 21     | Custom noise patterns                       | Customer Configuration       | V0       | Test            | 18         |
| 22     | Default Airbus profile                      | Customer Configuration       | V0       | Inspection      | 18         |
| 23     | Customer enumeration endpoint               | Customer Configuration       | V0       | Test            | 18         |
| 24     | Document persistence                        | Persistence                  | V0       | Test            | 6          |
| 25     | Node persistence                            | Persistence                  | V0       | Test            | 24         |
| 26     | Cascading deletion                          | Persistence                  | V0       | Test            | 25, 32     |
| 27     | Idempotent schema migration                 | Persistence                  | V0       | Test            | 24         |
| 28     | API versioning                              | REST API                     | V0       | Inspection      | —          |
| 29     | Document retrieval endpoint                 | REST API                     | V0       | Test            | 24         |
| 30     | Document listing endpoint                   | REST API                     | V0       | Test            | 24         |
| 31     | Processing status endpoint                  | REST API                     | V0       | Test            | 6          |
| 32     | Document deletion endpoint                  | REST API                     | V0       | Test            | 26         |
| 33     | Node update endpoint                        | REST API                     | V0       | Test            | 25         |
| 34     | OpenAPI documentation                       | REST API                     | V0       | Inspection      | 28         |
| 35     | Upload form                                 | Frontend Upload              | V0       | Demonstration   | 1          |
| 36     | Customer dropdown population                | Frontend Upload              | V0       | Demonstration   | 23, 35     |
| 37     | Processing progress modal                   | Frontend Upload              | V0       | Demonstration   | 31         |
| 38     | Dashboard document listing                  | Frontend Dashboard           | V0       | Demonstration   | 30         |
| 39     | Dashboard conformity chart                  | Frontend Dashboard           | V0       | Demonstration   | 38         |
| 40     | Dashboard deletion action                   | Frontend Dashboard           | V0       | Demonstration   | 32         |
| 41     | Ordered node table                          | Node Review                  | V0       | Demonstration   | 16, 29     |
| 42     | Markdown description rendering              | Node Review                  | V0       | Demonstration   | 41         |
| 43     | Inline applicability editing                | Node Review                  | V0       | Demonstration   | 33, 45     |
| 44     | Inline conformity editing                   | Node Review                  | V0       | Demonstration   | 33, 46     |
| 45     | Applicability values                        | Enumerations                 | V0       | Test            | —          |
| 46     | Conformity values                           | Enumerations                 | V0       | Test            | —          |
| 47     | Default values per node type                | Enumerations                 | V0       | Test            | 45, 46     |
| 48     | Extraction throughput                       | Performance                  | V0       | Test            | 7          |
| 49     | API responsiveness                          | Performance                  | V0       | Test            | 28         |
| 50     | Extraction failure containment              | Reliability                  | V0       | Test            | 6, 31      |
| 51     | Session isolation for background tasks      | Reliability                  | V0       | Inspection      | 6          |
| 52     | Input validation                            | Security                     | V0       | Test            | 28         |
| 53     | Markdown rendering sanitisation             | Security                     | V0       | Test            | 42         |
| 54     | Secret management                           | Security                     | V0       | Inspection      | —          |
| 55     | Light and dark themes                       | Usability                    | V0       | Demonstration   | —          |
| 56     | Responsive layout                           | Usability                    | V0       | Demonstration   | —          |
| 57     | Layered backend architecture                | Maintainability              | V0       | Inspection      | —          |
| 58     | Type hints coverage                         | Maintainability              | V0       | Analysis        | —          |
| 59     | Automated test coverage                     | Maintainability              | V0       | Analysis        | —          |
| 60     | Docker Compose deployment                   | Portability                  | V0       | Demonstration   | —          |
| 61     | Platform support                            | Portability                  | V0       | Test            | —          |
| 62     | JWT authentication                          | Future                       | V1       | Test            | —          |
| 63     | Real-time collaborative editing             | Future                       | V1       | Demonstration   | 33         |
| 64     | DOCX ingestion                              | Future                       | V2       | Test            | 1          |
| 65     | CSV export                                  | Future                       | V2       | Test            | 29         |
| 66     | Excel export                                | Future                       | V2       | Test            | 65         |
| 67     | Audit trail                                 | Future                       | V2       | Test            | 33         |
