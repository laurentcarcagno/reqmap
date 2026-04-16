---
name: documentation-writer
description: >
  Generates and maintains architecture documents, API specifications, user manuals,
  ADRs (Architecture Decision Records), and the model-context.md persistent memory file.
  Use when documenting features, creating user guides, updating API specs, recording
  architectural decisions, or maintaining the project's AI context file.
  NOT for writing application code, tests, or configuration files.
---
# Documentation Writer Skill

## Dispatch

| Request | Action |
|---------|--------|
| Document system architecture | → **Architecture Documentation** |
| Document API endpoints | → **API Documentation** |
| Write / update user manual | → **User Manuals** |
| Record a technical decision | → **Architecture Decision Records** |
| Update model-context.md | → **Model Context Document** |
| Document a component / module | → **Component Documentation** |
| Generate changelog / release notes | → **Release Documentation** |
| Empty / ambiguous | Ask for clarification |

---

## 1. Architecture Documentation

### Location
`docs/architecture/` — one file per bounded context or major subsystem.

### Template
```markdown
# <System/Subsystem Name> — Architecture Overview

## Purpose
<One paragraph describing what this system does and why it exists.>

## Context Diagram
<!-- Describe or reference a diagram showing external actors and system boundaries -->
<Suggest: C4 Context diagram. Tool: Mermaid, Excalidraw, or draw.io>
[📷 Place diagram here: `docs/architecture/diagrams/<name>-context.png`]

## Component Diagram
<!-- Internal components and their interactions -->
[📷 Place diagram here: `docs/architecture/diagrams/<name>-components.png`]

## Data Flow
1. User initiates <action> via <frontend component>.
2. Frontend calls `<API endpoint>`.
3. Backend validates input, calls `<service>`.
4. Service queries `<table>` via `<repository>`.
5. Response flows back through the stack.

## Key Technical Decisions
| Decision | Rationale | Date | ADR |
|----------|-----------|------|-----|
| <decision> | <why> | <YYYY-MM-DD> | [ADR-NNN](../adrs/NNN-<title>.md) |

## Dependencies
- **Internal:** <list of internal services/modules this depends on>
- **External:** <list of third-party services, APIs, databases>

## Non-Functional Requirements
- **Performance:** <SLA, latency targets>
- **Scalability:** <expected load, scaling strategy>
- **Security:** <auth model, data sensitivity classification>
```

### Rules
- Use **Mermaid** for inline diagrams in markdown. Use image files for complex diagrams.
- Always suggest **specific locations and filenames** for diagrams and screenshots.
- Update architecture docs whenever a new service, major component, or external integration is added.

---

## 2. API Documentation

### Approach: Schema-Driven
- **Preferred:** Generate OpenAPI 3.1 specs from Zod schemas or code annotations.
- **Fallback:** Maintain `docs/api/` markdown files with the template below.

### Endpoint Documentation Template
```markdown
## POST /api/v1/users

**Description:** Create a new user account.

**Authentication:** Required (Bearer token)  
**Authorization:** `admin` role only

### Request
**Headers:**
| Header | Required | Value |
|--------|----------|-------|
| `Authorization` | Yes | `Bearer <token>` |
| `Content-Type` | Yes | `application/json` |

**Body:**
```json
{
  "email": "user@example.com",
  "name": "Jane Doe",
  "role": "member"
}
```

**Validation Rules:**
| Field | Type | Constraints |
|-------|------|-------------|
| `email` | string | Required. Valid email. Max 320 chars. |
| `name` | string | Required. Min 1, max 255 chars. |
| `role` | string | Optional. One of: `member`, `admin`. Default: `member`. |

### Response

**201 Created:**
```json
{
  "data": {
    "id": "cuid_abc123",
    "email": "user@example.com",
    "name": "Jane Doe",
    "role": "member",
    "createdAt": "2025-03-15T14:30:00.000Z"
  }
}
```

**Error Responses:**
| Status | Code | When |
|--------|------|------|
| 400 | `BAD_REQUEST` | Invalid request body |
| 401 | `UNAUTHORIZED` | Missing or invalid token |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 409 | `CONFLICT` | Email already exists |
| 422 | `VALIDATION_ERROR` | Schema validation failed |
```

### Rules
- Document **every** public endpoint: method, path, auth, request schema, response schema, error codes.
- Include realistic example payloads (not `"string"` or `"test"`).
- Keep API docs in sync with code. Update docs in the same PR as the endpoint change.

---

## 3. User Manuals

### Location
`docs/user-guide/` — organized by feature area.

### Writing Guidelines
- Write in **plain language**. Assume the reader is a non-technical end user.
- Use **step-by-step numbered instructions** for task-based guides.
- Use **present tense** and **active voice** ("Click the Save button" not "The Save button should be clicked").
- **One task per section.** Don't combine unrelated instructions.
- Always suggest where to place **screenshots and illustrations**:
  ```markdown
  [📷 Screenshot: The dashboard showing the new widget. Place at `docs/user-guide/images/dashboard-widget.png`]
  ```
- Include **prerequisites** at the top of each guide (e.g., "You must be logged in as an admin").
- Include a **troubleshooting** section for common issues.

### Template
```markdown
# <Feature Name> — User Guide

## Prerequisites
- <List what the user needs before starting>

## Steps

### 1. <First Action>
<Describe what to do and what to expect.>

[📷 Screenshot: <description>. Place at `docs/user-guide/images/<feature>-step1.png`]

### 2. <Second Action>
<Describe what to do and what to expect.>

## Troubleshooting

| Problem | Solution |
|---------|----------|
| <symptom> | <fix or workaround> |
```

---

## 4. Architecture Decision Records (ADRs)

### Location
`docs/adrs/` — one file per decision.

### File Naming
`NNN-<kebab-case-title>.md` (e.g., `001-use-postgresql-over-mongodb.md`).

### Template (based on Michael Nygard format)
```markdown
# ADR-NNN: <Title>

**Status:** Proposed | Accepted | Deprecated | Superseded by [ADR-NNN]  
**Date:** YYYY-MM-DD  
**Deciders:** <names or roles>

## Context
<What is the issue or situation that requires a decision?>

## Decision
<What is the change that we're proposing or have agreed to implement?>

## Consequences

### Positive
- <benefit 1>
- <benefit 2>

### Negative
- <trade-off 1>
- <trade-off 2>

### Risks
- <risk and mitigation>

## Alternatives Considered
| Alternative | Pros | Cons | Reason for Rejection |
|------------|------|------|---------------------|
| <option A> | <pros> | <cons> | <why not chosen> |
```

### Rules
- Record **every** significant technical decision: framework choices, architectural patterns, third-party service selections, security model changes.
- ADRs are **immutable** once accepted. To change a decision, create a new ADR that supersedes the old one.
- Link ADRs from architecture docs and `model-context.md`.

---

## 5. Model Context Document

### Purpose
`model-context.md` is the AI assistant's **persistent memory** for the project. It captures domain knowledge, technical constraints, and project history so the AI can make consistent decisions across sessions.

### Location
Project root: `model-context.md`

### Template
```markdown
# Model Context — <Project Name>

> This file is the AI assistant's persistent memory for this project.
> Update it whenever significant decisions, constraints, or domain knowledge changes.
> Last updated: YYYY-MM-DD

## Project Overview
- **Name:** <project name>
- **Description:** <one-paragraph summary>
- **Tech Stack:** <frontend, backend, database, hosting>
- **Repository:** <URL>

## Domain Model
- **Core Entities:** <list primary domain objects and their relationships>
- **Business Rules:** <critical invariants the system must enforce>
- **Glossary:** <domain-specific terms and their definitions>

## Architecture Decisions
| Decision | Summary | ADR | Date |
|----------|---------|-----|------|
| <decision> | <one-line summary> | [ADR-NNN](docs/adrs/NNN-title.md) | YYYY-MM-DD |

## Technical Constraints
- <constraint 1: e.g., "Must support PostgreSQL 15+">
- <constraint 2: e.g., "All API responses must complete within 500ms">
- <constraint 3: e.g., "Must comply with GDPR for EU users">

## Active Conventions
- <convention 1: e.g., "All dates stored as UTC TIMESTAMPTZ">
- <convention 2: e.g., "Feature flags managed via environment variables">

## Known Technical Debt
| Item | Impact | Priority | Ticket |
|------|--------|----------|--------|
| <debt item> | <impact description> | High/Medium/Low | <link> |

## Recent Changes (Last 10)
| Date | Change | Commit/PR |
|------|--------|-----------|
| YYYY-MM-DD | <what changed> | <link> |

## Security Decisions
| Decision | Rationale | Date |
|----------|-----------|------|
| <e.g., "Use argon2id for password hashing"> | <why> | YYYY-MM-DD |
```

### Update Triggers
Update `model-context.md` when:
- A new feature is added or a major feature is modified.
- An architecture decision is made (add to decisions table + link ADR).
- A technical constraint is discovered or changed.
- A security-relevant decision is made.
- Technical debt is identified or resolved.

---

## 6. Component Documentation

### For Shared/Reusable Components
Document directly above the component export or in a co-located `README.md`:

```typescript
/**
 * DataTable — Sortable, filterable, paginated data table.
 *
 * @example
 * <DataTable
 *   columns={columns}
 *   data={users}
 *   searchKey="email"
 *   pagination={{ pageSize: 20 }}
 * />
 *
 * @see {@link docs/components/data-table.md} for full documentation
 */
```

### Rules
- Document **props**, **variants**, **events**, and **accessibility** behavior.
- Include at least one **usage example**.
- For design system components, link to the Storybook story or design spec.

---

## 7. Release Documentation

### Changelog Format (Keep a Changelog)
```markdown
# Changelog

## [1.2.0] — 2025-03-15

### Added
- OAuth2 PKCE login flow (#42)
- User profile avatar upload (#45)

### Changed
- Migrated from REST to GraphQL for user queries (#48)

### Fixed
- Cart quantity allowing negative values (#50)

### Security
- Upgraded jsonwebtoken to 9.0.1 to fix CVE-2023-XXXX (#51)
```

### Rules
- Generate changelog entries from Conventional Commit messages.
- Group by: Added, Changed, Deprecated, Removed, Fixed, Security.
- Link to PR/issue numbers for traceability.
- Include migration instructions for breaking changes.

---

## Critical Rules

1. Every PR that changes behavior must include documentation updates in the same PR.
2. Never write documentation that contradicts the code. If in doubt, read the code.
3. Always suggest specific file paths and locations for diagrams and screenshots.
4. Update `model-context.md` after every significant feature, decision, or constraint change.
5. ADRs are immutable once accepted. Supersede, never edit.
6. API documentation must match the actual request/response schemas exactly.
7. User guides must be written for non-technical users in plain language.
