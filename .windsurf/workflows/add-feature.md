---
description: Given a feature request, produce a scoped agile implementation plan and guide full-stack implementation using relevant skills, enforcing develop → test → commit cycles at every step.
---
# Add Feature Workflow

## Prerequisites
- Feature request or user story is provided.
- `model-context.md` is available for project context.
- Development environment is set up and test suite is runnable.

## Steps

### 1. Analyze & Scope the Feature
- Read the feature request carefully. Identify:
  - **User value:** What problem does this solve? Who benefits?
  - **Affected layers:** Database / Backend / Frontend / Infrastructure.
  - **Affected existing code:** Which modules, components, or endpoints are impacted?
- Check `model-context.md` for relevant constraints, conventions, and existing architecture.
- List **assumptions** and clarify ambiguities with the user before proceeding.
- Define **acceptance criteria** (specific, testable conditions that prove the feature works).

### 2. Create the Implementation Plan
Invoke the `/create-development-plan` workflow mindset to structure work:

```markdown
## Feature: <Feature Name>

### Acceptance Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>
- [ ] <criterion 3>

### Implementation Tasks (ordered by dependency)
1. Database changes (if any)
2. Backend API endpoints / logic
3. Frontend components / pages
4. Security hardening
5. Testing (unit + integration + E2E)
6. Documentation updates
```

Present the plan to the user for approval before implementing.

### 3. Database Layer (if applicable)
Invoke the `@database-management` skill:
- Design or modify the schema (tables, columns, constraints, indexes).
- Generate a reversible migration (`up` + `down`).
- Test the migration locally in both directions.
- Verify data integrity constraints (NOT NULL, FOREIGN KEY, CHECK).
- Write seed data for the new entities (if needed for development/testing).

**Gate:**
- [ ] Migration runs cleanly (`up` and `down`).
- [ ] Existing tests still pass.
- [ ] Commit: `feat(db): add <table/column> for <feature>`

### 4. Backend Layer (if applicable)
Invoke the `@backend-development` skill:
- Design API endpoints following REST conventions (method, path, status codes).
- Define Zod/Pydantic request and response schemas.
- Implement validation middleware for each endpoint.
- Implement the service layer with business logic (framework-agnostic).
- Implement the repository layer for data access.
- Add authentication and authorization middleware to protected routes.
- Add structured logging with requestId correlation.

**Testing:**
- Write unit tests for the service layer (mock repositories).
- Write integration tests for API endpoints (test full request → response cycle).
- Test error paths: invalid input (422), unauthorized (401), forbidden (403), not found (404).

**Gate:**
- [ ] All new and existing backend tests pass.
- [ ] API returns correct status codes and response shapes.
- [ ] No internal details leaked in error responses.
- [ ] Commit: `feat(api): add <endpoint> for <feature>`

### 5. Frontend Layer (if applicable)
Invoke the `@frontend-development` skill:
- Design the component hierarchy (container → presentational → primitives).
- Build components using TypeScript, Tailwind CSS, and shadcn/ui.
- Implement state management following the decision matrix:
  - Server state → TanStack Query / RSC
  - Form state → React Hook Form + Zod
  - UI state → useState / Zustand
- Handle all four async states: loading (skeleton), success, empty, error (with retry).
- Ensure responsive design: mobile-first, tested at 320px/768px/1024px/1440px.
- Ensure accessibility: keyboard navigation, ARIA labels, semantic HTML, color contrast.
- Implement i18n: use translation keys for all user-facing strings.

**Testing:**
- Write unit tests for component logic and hooks.
- Write interaction tests for user flows (click, type, submit).
- Run accessibility checks (axe-core).

**Gate:**
- [ ] All new and existing frontend tests pass.
- [ ] UI is responsive and accessible.
- [ ] Loading, error, empty, and success states render correctly.
- [ ] Commit: `feat(ui): add <component/page> for <feature>`

### 6. Security Review
Invoke the `@security-hardening` skill:
- [ ] New endpoints have authentication + authorization.
- [ ] Input validation is applied at the API boundary.
- [ ] No secrets or sensitive data exposed to the client.
- [ ] File uploads (if any) validated for MIME type, size, and stored securely.
- [ ] CORS headers configured correctly for new endpoints.
- [ ] Rate limiting applied to new public-facing endpoints.

**Gate:**
- [ ] Security checklist passes.
- [ ] Commit (if separate changes needed): `fix(security): harden <feature> endpoints`

### 7. End-to-End Testing
- Write E2E tests for the critical user journey of this feature using Playwright/Cypress.
- Test the happy path end-to-end (frontend → API → database → response → UI update).
- Test primary error paths (network failure, validation error, auth failure).

**Gate:**
// turbo
- Run: `npx playwright test` or `npx cypress run` — all E2E tests must pass.
- [ ] Commit: `test(e2e): add <feature> journey tests`

### 8. Documentation
Invoke the `@documentation-writer` skill:
- [ ] **API docs:** Document new/changed endpoints (method, path, auth, request/response schemas, error codes).
- [ ] **Architecture docs:** Update if new services, components, or integrations were added.
- [ ] **User manual:** Write step-by-step instructions for the new feature. Suggest screenshot placements.
- [ ] **model-context.md:** Record new domain entities, business rules, technical decisions, and constraints.
- [ ] **ADR:** Create an Architecture Decision Record if a significant technical choice was made.

**Gate:**
- [ ] Documentation is complete and accurate.
- [ ] Commit: `docs: add documentation for <feature>`

### 9. Final Verification
- [ ] Run the full test suite (unit + integration + E2E) — zero failures.
- [ ] Run linter and type-checker — zero errors.
- [ ] Run security audit (`npm audit` / `pip-audit`) — no critical/high issues.
- [ ] Review all commits follow Conventional Commits format.
- [ ] PR description includes: What, Why, How to Test, Screenshots (if UI).

### 10. Summary
Output a feature implementation summary:

```markdown
## Feature Complete: <Feature Name>

**Commits:**
1. `feat(db): ...`
2. `feat(api): ...`
3. `feat(ui): ...`
4. `test(e2e): ...`
5. `docs: ...`

**Files changed:** <count>
**Tests added:** <count> unit, <count> integration, <count> E2E
**Documentation updated:** <list of files>
**Acceptance criteria met:** <all / partial — list any gaps>
```
