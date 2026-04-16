---
trigger: always_on
---
# Project Engineering Standards

These rules apply to **every** file, commit, and review across the entire codebase. They are non-negotiable and must never be weakened by skill or workflow overrides.

---

## 1. Code Quality Principles

| Principle | Enforcement |
|-----------|-------------|
| **SOLID** | Single responsibility per module/component. Depend on abstractions. Open for extension, closed for modification. |
| **DRY** | Extract shared logic into well-named utilities. Never copy-paste blocks of code. |
| **KISS** | Choose the simplest solution that meets the requirement. Reject clever code in favour of clear code. |
| **YAGNI** | Do not build abstractions, wrappers, or features that are not required by the current task. |
| **Least Surprise** | APIs, props, and function signatures must behave as their names suggest. |

### Performance
- Measure before optimizing. Use profiling tools, not intuition.
- Lazy-load heavy modules, images, and routes.
- Prefer streaming and pagination over unbounded data fetches.

### Error Handling
- Never swallow exceptions silently. Every `catch` must log or re-throw with context.
- Distinguish **operational errors** (expected: network timeout, invalid input) from **programmer errors** (unexpected: null reference, type mismatch). Operational errors are handled; programmer errors crash loudly in dev and report in production.
- Return structured error responses from APIs: `{ error: { code, message, details? } }`.

---

## 2. Language & Framework Conventions

### TypeScript (Strict Mode Required)
- Enable `strict: true`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes` in `tsconfig.json`.
- Prefer `interface` for object shapes; use `type` for unions, intersections, and mapped types.
- Never use `any`. Use `unknown` + type narrowing when the type is genuinely unknown.
- Prefer `const` assertions and discriminated unions over loose string enums.
- All public functions must have explicit return types.

### React / Next.js
- **Functional components only.** No class components.
- **Declarative JSX.** Avoid imperative DOM manipulation.
- **Minimize `useEffect`.** Prefer derived state, React Server Components (RSC), or server actions.
- **Component file structure:** one exported component per file, co-located with its types, tests, and styles.
- **Naming:** PascalCase for components, camelCase for hooks (`useAuth`), kebab-case for file/folder names.
- Use **Zod** for all runtime schema validation (forms, API responses, env vars).

### Node.js / Express / Fastify Backend
- Strict TypeScript. No `require()` — use ESM imports.
- Define request/response schemas with Zod; generate OpenAPI specs from schemas.
- All endpoints must be **stateless**. Session state belongs in a store (Redis, DB), never in-memory.
- Use async/await exclusively. No raw callbacks or unhandled promise rejections.

### Python Backend (FastAPI / Django)
- Type hints on all function signatures. Use Pydantic v2 models for request/response validation.
- Follow PEP 8. Use `ruff` for linting and formatting.
- Structure projects with clean separation: `routers/`, `services/`, `repositories/`, `schemas/`.

### CSS / Styling
- **Tailwind CSS** as the default utility framework. Use design tokens via `tailwind.config`.
- **shadcn/ui** for component primitives. Extend, don't fork.
- No inline styles except for truly dynamic values (e.g., computed positions).
- Maintain a single source of truth for colors, spacing, typography, and breakpoints.

---

## 3. Version Control Practices

### Commits
- **Atomic commits:** one logical change per commit. Never mix refactoring with feature work.
- **Conventional Commits** format is mandatory:
  ```
  <type>(<optional scope>): <imperative verb> <description>
  ```
  Valid types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`, `ci`, `build`, `style`.
  Examples:
  - `feat(auth): add OAuth2 PKCE login flow`
  - `fix(cart): prevent negative quantity on decrement`
  - `refactor(api): extract validation middleware`
- Commit message body (optional) explains **why**, not **what**.
- **Never commit** code that fails linting, type-checking, or the test suite.

### Branching
- `main` — production-ready, protected. Deploys automatically.
- `develop` — integration branch (if used). Always green.
- Feature branches: `feat/<ticket>-<short-description>` (e.g., `feat/AUTH-42-oauth-pkce`).
- Bugfix branches: `fix/<ticket>-<short-description>`.
- Hotfix branches: `hotfix/<ticket>-<short-description>` (branch from `main`).

### Pull Requests
- Title follows Conventional Commits format.
- Description includes: **What** changed, **Why**, **How to test**, **Screenshots** (for UI changes).
- All PRs require at least one peer review approval.
- All CI checks (lint, type-check, test, build) must pass before merge.
- Squash-merge feature branches into `main`/`develop`.

---

## 4. Testing Requirements

### Strategy
- **Test pyramid:** many unit tests → fewer integration tests → minimal E2E tests.
- **Test-Driven Development (TDD):** write the failing test first for all business logic.
- Tests are first-class code — same quality standards, same review process.

### Coverage Targets
| Layer | Minimum Coverage | Tool |
|-------|-----------------|------|
| Business logic / utilities | 90% line coverage | Vitest / Jest / pytest |
| API endpoints | 80% line coverage | Supertest / httpx |
| Critical user journeys | All happy + primary error paths | Playwright / Cypress |

### Naming Convention
- Test files: `<module>.test.ts` or `<module>.spec.ts` (co-located with source).
- Test names: `it('should <expected behavior> when <condition>')`.

### Rules
- No tests that depend on execution order or shared mutable state.
- Mock external services and databases at the boundary; never mock the unit under test.
- Snapshot tests are allowed only for serializable output (e.g., API responses), never for UI.
- **Gate:** code cannot be committed unless `npm test` / `pytest` passes locally with zero failures.

---

## 5. Project Structure (Recommended)

```
project-root/
├── .windsurf/              # AI assistant configuration
│   ├── rules/              # Always-on rules (this file)
│   ├── skills/             # Skill definitions
│   └── workflows/          # Workflow definitions
├── src/
│   ├── app/                # Next.js App Router / main app entry
│   ├── components/         # Shared UI components
│   │   ├── ui/             # Primitive components (shadcn/ui)
│   │   └── features/       # Feature-specific compound components
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # Shared utilities, helpers, constants
│   ├── server/             # Backend: routes, controllers, services
│   │   ├── routes/         # API route handlers
│   │   ├── services/       # Business logic layer
│   │   ├── repositories/   # Data access layer
│   │   └── middleware/      # Auth, validation, error handling
│   ├── schemas/            # Zod / Pydantic validation schemas
│   ├── types/              # Shared TypeScript type definitions
│   └── styles/             # Global styles, Tailwind config
├── prisma/                 # Database schema & migrations (if using Prisma)
├── tests/                  # Integration & E2E tests
├── docs/                   # Architecture docs, ADRs, user manuals
├── model-context.md        # AI persistent memory / project context
└── README.md
```

---

## 6. Dependency Management

- **Lock files** (`package-lock.json`, `pnpm-lock.yaml`, `poetry.lock`) are always committed.
- Pin exact versions for production dependencies. Use ranges only for dev dependencies.
- Audit dependencies monthly: `npm audit`, `pnpm audit`, or `pip-audit`.
- Maximum dependency age: 6 months behind latest. Automate with Renovate or Dependabot.
- Evaluate every new dependency against: bundle size, maintenance activity, security history, license.

---

## 7. Environment & Configuration

- All configuration via environment variables. Use `.env.example` as a committed template (never commit `.env`).
- Validate all env vars at startup using Zod (`z.object({...}).parse(process.env)`).
- Three mandatory environments: `development`, `staging`, `production`.
- Secrets must never appear in logs, error messages, or client-side bundles.

---

## 8. Accessibility & Internationalization

- **WCAG 2.1 AA** compliance is the minimum bar for all user-facing UI.
- All interactive elements must be keyboard-navigable and have visible focus indicators.
- All images must have meaningful `alt` text (or `alt=""` for decorative images).
- Use semantic HTML elements (`<nav>`, `<main>`, `<article>`, `<button>`) — never `<div onClick>`.
- Structure all user-facing strings for i18n extraction (e.g., `next-intl`, `react-i18next`).
- Support RTL layouts via logical CSS properties (`margin-inline-start` instead of `margin-left`).
