---
description: Review and audit frontend and backend changes for compliance with project standards, security, testing, and documentation requirements.
---
# Code Review Workflow

## Prerequisites
- Changes are committed or staged (diff is available).
- Test suite is runnable locally.

## Steps

### 1. Gather Context
- Read the current diff (`git diff` or `git diff --staged`).
- Identify which layers are affected: frontend, backend, database, infrastructure.
- List all modified, added, and deleted files.

### 2. Verify Project Standards Compliance
For each changed file, verify against `.windsurf/rules/project_standards.md`:

**Code Quality:**
- [ ] Follows SOLID, DRY, KISS, YAGNI principles.
- [ ] No unnecessary abstractions or dead code introduced.
- [ ] Error handling is complete (no swallowed exceptions, structured error responses).
- [ ] All functions have explicit return types (TypeScript) or type hints (Python).
- [ ] No use of `any` in TypeScript. No raw callbacks.

**Formatting & Naming:**
- [ ] File naming follows conventions (kebab-case for files, PascalCase for components).
- [ ] Variable and function naming is descriptive and consistent.
- [ ] No hardcoded values — uses environment variables or configuration.

### 3. Frontend Review (if applicable)
Invoke the `@frontend-development` skill checklist:
- [ ] Functional components only, no class components.
- [ ] State management follows the decision matrix (server state via TanStack Query, form state via React Hook Form, etc.).
- [ ] No `useEffect` for data fetching — uses RSC, server actions, or query hooks.
- [ ] Responsive design: mobile-first, tested at 320px/768px/1024px/1440px.
- [ ] Accessibility: keyboard navigation, ARIA labels, color contrast ≥ 4.5:1, semantic HTML.
- [ ] Loading, error, empty, and success states handled for every async UI.
- [ ] No hardcoded colors/spacing — uses Tailwind design tokens.
- [ ] i18n: no hardcoded user-facing strings.

### 4. Backend Review (if applicable)
Invoke the `@backend-development` skill checklist:
- [ ] API endpoints follow REST conventions (proper HTTP methods, status codes, resource naming).
- [ ] Input validation at the boundary using Zod/Pydantic schemas.
- [ ] Authentication middleware on all protected routes.
- [ ] Authorization checks include resource-level ownership (BOLA prevention).
- [ ] Error responses use the standard envelope: `{ error: { code, message, details? } }`.
- [ ] No internal details leaked in error messages (stack traces, DB errors, file paths).
- [ ] Structured logging with requestId correlation.
- [ ] External calls have timeouts and retry strategies.

### 5. Database Review (if applicable)
Invoke the `@database-management` skill checklist:
- [ ] Migration is reversible (has both `up` and `down`).
- [ ] Migration tested locally in both directions.
- [ ] New columns have appropriate `NOT NULL`, `DEFAULT`, and `CHECK` constraints.
- [ ] Foreign key columns are indexed.
- [ ] No raw SQL string interpolation — parameterized queries only.
- [ ] Transactions used for multi-table mutations.

### 6. Security Review
Invoke the `@security-hardening` skill checklist:
- [ ] No secrets or credentials in code or config files.
- [ ] Input sanitization applied (trim, normalize, strip control characters).
- [ ] CORS and security headers configured correctly.
- [ ] File uploads validated (MIME type, size, random filenames).
- [ ] Auth changes reviewed by a second person.
- [ ] Dependencies: `npm audit` / `pip-audit` shows no critical/high vulnerabilities.

### 7. Testing Verification
- [ ] New business logic has unit tests.
- [ ] New API endpoints have integration tests.
- [ ] Critical user journeys have E2E coverage.
- [ ] Tests follow naming convention: `it('should <behavior> when <condition>')`.
- [ ] No tests depend on execution order or shared mutable state.
- [ ] Test suite passes locally with zero failures.
// turbo
- Run: `npm test` or `pytest` to verify all tests pass.

### 8. Documentation Update
Invoke the `@documentation-writer` skill:
- [ ] API documentation updated for new/changed endpoints.
- [ ] Architecture documentation updated for new components or services.
- [ ] User manual updated for user-facing feature changes (with screenshot placement suggestions).
- [ ] `model-context.md` updated with new decisions, constraints, or domain knowledge.
- [ ] ADR created for any significant technical decision made in this change.

### 9. Commit & PR Quality
- [ ] Commit messages follow Conventional Commits format.
- [ ] Commits are atomic (one logical change each).
- [ ] PR title follows Conventional Commits format.
- [ ] PR description includes: What, Why, How to Test, Screenshots (if UI).

### 10. Generate Review Summary
Output a structured review report:

```markdown
# Code Review Summary

## Overview
- **Files changed:** <count>
- **Lines added/removed:** +<added> / -<removed>
- **Layers affected:** Frontend / Backend / Database / Infrastructure

## Compliance Status
| Category | Status | Issues |
|----------|--------|--------|
| Code Quality | ✅ Pass / ⚠️ Warning / ❌ Fail | <details> |
| Security | ✅ / ⚠️ / ❌ | <details> |
| Testing | ✅ / ⚠️ / ❌ | <details> |
| Accessibility | ✅ / ⚠️ / ❌ | <details> |
| Documentation | ✅ / ⚠️ / ❌ | <details> |
| Commit Hygiene | ✅ / ⚠️ / ❌ | <details> |

## Issues Found
### Critical (must fix before merge)
1. <issue description + file + line>

### Warnings (should fix, non-blocking)
1. <issue description + file + line>

### Suggestions (nice to have)
1. <suggestion>

## Verdict
**APPROVE** / **REQUEST CHANGES** / **NEEDS DISCUSSION**
```
