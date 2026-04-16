---
description: Plan and execute UI/UX refactors focused on visual design, theming, layout, and accessibility while preserving existing behavior. Ensures documentation and model context are updated.
---
# Refactor Design Workflow

## Prerequisites
- Target components or pages for refactoring are identified.
- Design system tokens are defined in `tailwind.config.ts`.
- Existing test suite covers the behavior of the components being refactored.
- If tests are missing, write them **before** refactoring to establish a behavioral baseline.

## Steps

### 1. Assess Current State
- Identify all components and pages targeted for refactoring.
- For each component, document:
  - **Current visual state:** take screenshots or describe the layout.
  - **Current behavior:** list interactions (click, hover, focus, keyboard, screen reader).
  - **Current test coverage:** identify which behaviors are tested.
  - **Known issues:** list visual bugs, accessibility failures, responsive breakage.
- Run the existing test suite to establish a green baseline.

**Gate:**
- [ ] All existing tests pass before any changes are made.
- [ ] Behavioral baseline is documented.

### 2. Create Refactoring Design Spec
Define the target state for the refactor, aligned with the project's design system:

```markdown
## Refactor Spec: <Component/Page Name>

### Goals
- [ ] <Goal 1: e.g., "Align spacing to 4px grid system">
- [ ] <Goal 2: e.g., "Implement dark mode support">
- [ ] <Goal 3: e.g., "Fix accessibility failures (contrast, focus)">

### Design Tokens to Apply
| Token | Current Value | Target Value |
|-------|--------------|--------------|
| Background | `bg-gray-100` | `bg-background` (semantic) |
| Text | `text-gray-800` | `text-foreground` (semantic) |
| Border radius | `rounded-md` | `rounded-lg` (design system) |

### Responsive Behavior
| Breakpoint | Layout Change |
|------------|--------------|
| Mobile (< 640px) | <description> |
| Tablet (640–1024px) | <description> |
| Desktop (> 1024px) | <description> |

### Accessibility Fixes
- [ ] <Fix 1: e.g., "Add visible focus ring to all buttons">
- [ ] <Fix 2: e.g., "Increase contrast ratio on muted text to 4.5:1">

### Out of Scope
- <Explicitly list what NOT to change: e.g., "Do not change data fetching logic">
- <e.g., "Do not modify API contracts or state management patterns">
```

Present the spec to the user for approval before implementing.

### 3. Write Missing Behavioral Tests
Before changing any visual code, ensure every **interaction and state** is covered by tests:
- Component renders correctly with default props.
- Component renders all variants (loading, error, empty, success).
- Interactive behaviors work (click handlers fire, forms submit, modals open/close).
- Keyboard navigation works (Tab, Enter, Escape, Arrow keys).
- Screen reader announcements are correct (ARIA attributes, live regions).

**Gate:**
- [ ] All behavioral tests pass.
- [ ] Commit: `test(ui): add baseline tests for <component> before refactor`

### 4. Execute the Refactor
Invoke the `@frontend-development` skill with these constraints:

**Allowed changes (visual only):**
- [ ] Replace hardcoded colors/spacing with design system tokens.
- [ ] Update Tailwind classes for consistent theming (light/dark mode).
- [ ] Restructure layout for responsive behavior (mobile-first).
- [ ] Add/fix CSS transitions and animations (respect `prefers-reduced-motion`).
- [ ] Fix accessibility issues (focus indicators, contrast, ARIA, semantic HTML).
- [ ] Update i18n: replace any hardcoded strings with translation keys.
- [ ] Apply shadcn/ui component variants where appropriate.

**Forbidden changes (preserve behavior):**
- ❌ Do not change component props interfaces.
- ❌ Do not change state management logic.
- ❌ Do not change data fetching patterns.
- ❌ Do not change event handler business logic.
- ❌ Do not change API contracts or route structures.
- ❌ Do not rename exported components (breaking change).

### 5. Verify No Behavioral Regressions
// turbo
Run the full test suite:
- `npm test` — all unit and integration tests must pass.
- `npx playwright test` — all E2E tests must pass (if applicable).

Additional verification:
- [ ] Visual comparison: compare before/after screenshots at 320px, 768px, 1024px, 1440px.
- [ ] Dark mode: verify all refactored components render correctly in dark theme.
- [ ] Accessibility: run `axe-core` audit — zero violations.
- [ ] Animation: verify `prefers-reduced-motion` disables all non-essential animations.
- [ ] i18n: verify translation keys render correctly in at least two locales.

**Gate:**
- [ ] Zero test failures.
- [ ] Zero accessibility violations.
- [ ] Visual output matches the design spec.
- [ ] Commit: `refactor(ui): update <component> to use design system tokens`

### 6. Update Documentation
Invoke the `@documentation-writer` skill:

- [ ] **Component docs:** Update props documentation, variant descriptions, and usage examples.
- [ ] **Storybook:** Update stories to reflect new variants and visual states (if using Storybook).
- [ ] **Design system docs:** Document any new tokens, patterns, or conventions introduced.
- [ ] **model-context.md:** Record the design refactor decision:
  ```markdown
  | Date | Change | Commit/PR |
  |------|--------|-----------|
  | YYYY-MM-DD | Refactored <component> to use semantic design tokens, added dark mode support | PR #<number> |
  ```
- [ ] **ADR:** If the refactor establishes a new design pattern or convention, create an ADR.

**Gate:**
- [ ] Documentation is complete.
- [ ] Commit: `docs: update component documentation after <component> refactor`

### 7. Summary
Output a refactor summary:

```markdown
## Refactor Complete: <Component/Page Name>

### Changes Made
- <Change 1: e.g., "Migrated 12 color values to semantic tokens">
- <Change 2: e.g., "Added dark mode support to all card variants">
- <Change 3: e.g., "Fixed 3 WCAG contrast failures">

### Behavioral Verification
- Unit tests: <count> pass / 0 fail
- E2E tests: <count> pass / 0 fail
- Accessibility: 0 violations (axe-core)

### Files Changed
- <list of files>

### Commits
1. `test(ui): add baseline tests for <component> before refactor`
2. `refactor(ui): update <component> to use design system tokens`
3. `docs: update component documentation after <component> refactor`

### Design Patterns Established
- <Any new conventions that should be applied to other components>
```
