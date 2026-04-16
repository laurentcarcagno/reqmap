---
name: frontend-development
description: >
  Implements frontend UI/UX with React, Next.js, Tailwind CSS, and shadcn/ui.
  Covers component architecture, state management, responsive layouts, accessibility,
  performance optimization, and internationalization.
  Use when building UI components, pages, layouts, managing client state, implementing
  forms, adding animations, or improving accessibility and i18n.
  NOT for API route handlers (backend-development), database queries (database-management),
  or infrastructure/deployment concerns.
---
# Frontend Development Skill

## Dispatch

| Request | Action |
|---------|--------|
| Build a new component / page | → **Component Architecture** + **Styling** |
| Add or refactor a form | → **Forms & Validation** |
| Fix layout / responsive issue | → **Responsive Design** |
| Improve accessibility | → **Accessibility** |
| Add or fix state management | → **State Management** |
| Optimize performance / Core Web Vitals | → **Performance** |
| Add i18n / localization | → **Internationalization** |
| Implement animation / transition | → **Animation** |
| Empty / ambiguous | Ask for clarification |

---

## 1. Component Architecture

### File Structure
Every component lives in its own directory with co-located files:
```
components/features/user-profile/
├── user-profile.tsx          # Component implementation
├── user-profile.test.tsx     # Unit / interaction tests
├── user-profile.stories.tsx  # Storybook story (optional)
├── use-user-profile.ts       # Component-specific hook (if needed)
└── index.ts                  # Public barrel export
```

### Component Design Rules
- **One exported component per file.** Internal sub-components are fine if not reused elsewhere.
- **Props interface** defined at the top of the file, named `<Component>Props`.
- **Explicit return types** on all components: `function UserProfile(props: UserProfileProps): React.ReactElement`.
- **Composition over configuration:** prefer `children` and render props over deeply nested config objects.
- **Compound component pattern** for complex widgets (e.g., `<Tabs>`, `<Tabs.List>`, `<Tabs.Panel>`).
- **Separation of concerns:**
  - **Container components** fetch data and manage state.
  - **Presentational components** receive props and render UI.
  - Prefer React Server Components (RSC) for data-fetching containers in Next.js App Router.

### Component Hierarchy
```
Layout (RSC) → Page (RSC) → Feature Container (RSC or Client) → UI Primitives (Client)
```

### Naming Conventions
| Entity | Convention | Example |
|--------|-----------|---------|
| Component | PascalCase | `UserProfile` |
| File / folder | kebab-case | `user-profile.tsx` |
| Hook | camelCase, `use` prefix | `useAuth` |
| Constant | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Event handler prop | `on` prefix | `onSubmit`, `onClick` |
| Boolean prop | `is`/`has`/`should` prefix | `isLoading`, `hasError` |

---

## 2. State Management

### Decision Matrix
| State Type | Solution | Example |
|------------|----------|---------|
| **Server state** (async, cacheable) | TanStack Query / SWR / RSC | API data, user profile |
| **URL state** (shareable, bookmarkable) | URL search params (`nuqs`, `useSearchParams`) | Filters, pagination, tabs |
| **Form state** (ephemeral, per-form) | React Hook Form + Zod resolver | Login form, checkout |
| **Local UI state** (component-scoped) | `useState` / `useReducer` | Dropdowns, modals, toggles |
| **Shared client state** (cross-component) | Zustand (small) / Redux Toolkit (large) | Shopping cart, notifications |
| **Theme / global config** | React Context (read-heavy, write-rare) | Theme, locale, feature flags |

### Rules
- **Never store derived state.** Compute it inline or with `useMemo`.
- **Never duplicate server state** in client stores. Let the query cache be the source of truth.
- **Minimize `useEffect`:** most side effects should be event handlers, server actions, or query invalidations.
- **Lift state only as far as needed.** Start local; promote only when a sibling genuinely needs it.

---

## 3. Forms & Validation

### Stack
- **React Hook Form** for form state and submission lifecycle.
- **Zod** for schema definition and validation.
- **`@hookform/resolvers/zod`** to bridge them.

### Rules
- Define the Zod schema **first**, then derive the TypeScript type with `z.infer<typeof schema>`.
- Validate **client-side** for instant UX feedback and **server-side** for security (never trust the client).
- Show inline field-level errors immediately on blur; show summary errors on submit.
- Disable the submit button while `isSubmitting` is true. Show a loading indicator.
- Handle server-returned field errors by mapping them back to `setError()`.

### Example Pattern
```typescript
const loginSchema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'Minimum 8 characters'),
});
type LoginValues = z.infer<typeof loginSchema>;
```

---

## 4. Styling & Design System

### Tailwind CSS
- Use the project's `tailwind.config.ts` as the **single source of truth** for design tokens (colors, spacing, typography, breakpoints, shadows).
- Prefer semantic token names (`bg-primary`, `text-muted-foreground`) over raw values (`bg-blue-500`).
- Use `clsx` or `cn()` utility (from shadcn/ui) for conditional class merging.
- Extract repeated class combinations into component variants using `cva` (class-variance-authority).

### shadcn/ui
- Use as the base component library. Extend via the `cn()` utility and variant props — **never fork** the source files unless absolutely necessary.
- When customizing, add new variants to the existing component rather than creating wrappers.

### Rules
- No inline `style={{}}` except for truly dynamic computed values (e.g., `style={{ left: `${x}px` }}`).
- No CSS modules or styled-components in new code. Tailwind utilities only.
- Dark mode: support via Tailwind `dark:` variants and a `ThemeProvider`. Default to system preference.

---

## 5. Responsive Design

### Approach: Mobile-First
- Write base styles for mobile; add complexity at larger breakpoints.
- Tailwind breakpoints: `sm` (640px), `md` (768px), `lg` (1024px), `xl` (1280px), `2xl` (1536px).

### Layout Patterns
| Pattern | Use Case | Implementation |
|---------|----------|----------------|
| **Stack** | Vertical list of elements | `flex flex-col gap-4` |
| **Cluster** | Horizontal wrapping items | `flex flex-wrap gap-2` |
| **Sidebar** | Main content + sidebar | `grid grid-cols-1 lg:grid-cols-[280px_1fr]` |
| **Grid** | Card grids, galleries | `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6` |

### Rules
- Use `rem`/`em` for sizing, never `px` (except for borders and shadows).
- Test at 320px, 768px, 1024px, 1440px viewports minimum.
- All touch targets must be at least 44×44px (WCAG 2.5.8).
- Avoid horizontal scroll on any viewport. Use overflow-hidden + truncation for long content.

---

## 6. Accessibility (WCAG 2.1 AA)

### Mandatory Checklist
- [ ] All interactive elements reachable and operable via keyboard (Tab, Enter, Escape, Arrow keys).
- [ ] Visible focus indicators on all focusable elements (never `outline-none` without a replacement).
- [ ] All images have `alt` text (descriptive for informative, `alt=""` for decorative).
- [ ] Color contrast: **4.5:1** for normal text, **3:1** for large text and UI components.
- [ ] Form inputs have associated `<label>` elements (not just placeholder text).
- [ ] Error messages are programmatically associated with their inputs via `aria-describedby`.
- [ ] Dynamic content changes announced via `aria-live` regions.
- [ ] Modals trap focus and return focus to trigger on close.
- [ ] No content conveyed by color alone.
- [ ] Page has a logical heading hierarchy (`h1` → `h2` → `h3`, no skipped levels).

### Semantic HTML Priority
Use native HTML elements before reaching for ARIA:
```
<button>   instead of   <div role="button" tabIndex={0} onClick={...}>
<a href>   instead of   <span onClick={navigate}>
<nav>      instead of   <div class="navigation">
<dialog>   instead of   <div class="modal">
```

### Testing
- Run `axe-core` (via `@axe-core/react` or Playwright `axe`) in CI.
- Manual screen reader testing for critical flows (VoiceOver, NVDA).

---

## 7. Performance Optimization

### Core Web Vitals Targets
| Metric | Target | Technique |
|--------|--------|-----------|
| **LCP** (Largest Contentful Paint) | < 2.5s | Optimize hero images, use `priority` on `<Image>`, preload fonts |
| **INP** (Interaction to Next Paint) | < 200ms | Avoid long tasks, use `useTransition` for non-urgent updates |
| **CLS** (Cumulative Layout Shift) | < 0.1 | Set explicit `width`/`height` on images, avoid layout-shifting injections |

### Techniques
- **Code splitting:** `React.lazy()` + `Suspense` for route-level and feature-level splits.
- **Image optimization:** Use `next/image` with `sizes` attribute. Serve WebP/AVIF. Lazy-load below-fold images.
- **Bundle analysis:** Run `next build --analyze` or `source-map-explorer` before every release.
- **Memoization:** Use `React.memo` only when profiling shows unnecessary re-renders. Never premature-optimize.
- **Virtualization:** Use `@tanstack/react-virtual` for lists exceeding 100 items.
- **Font loading:** Use `next/font` for self-hosted fonts with `display: swap`.

---

## 8. Internationalization (i18n)

### Stack
- **next-intl** (Next.js) or **react-i18next** (generic React).
- ICU MessageFormat for plurals, gender, and interpolation.

### Rules
- Never hardcode user-facing strings. Always use translation keys.
- Key naming: `<namespace>.<section>.<element>` (e.g., `auth.login.submitButton`).
- Co-locate translation files per locale: `messages/en.json`, `messages/fr.json`.
- Support RTL layouts: use CSS logical properties (`margin-inline-start`, `padding-block-end`).
- Format dates, numbers, and currencies with `Intl` APIs — never manually.
- Default locale: `en`. Add new locales via the translation workflow, not ad-hoc strings.

---

## 9. Animation & Transitions

### Stack
- **CSS transitions** for simple hover/focus effects.
- **Framer Motion** for complex enter/exit animations, layout animations, and gesture-driven interactions.
- **Tailwind `animate-*`** utilities for predefined keyframe animations (spin, pulse, bounce).

### Rules
- Animate only `transform` and `opacity` for 60fps performance. Avoid animating `width`, `height`, `top`, `left`.
- Always respect `prefers-reduced-motion`: wrap animations in a media query or Framer Motion's `useReducedMotion`.
- Entry animations: 150–300ms. Exit animations: 100–200ms. Spring physics for natural feel.
- Never block user interaction with an animation. Ensure controls are usable during transitions.

---

## 10. Error & Loading States

### Every async UI must handle four states:
1. **Loading** — skeleton placeholder or spinner (never blank screen).
2. **Success** — render data.
3. **Empty** — friendly message with call-to-action (e.g., "No results found. Try a different search.").
4. **Error** — user-friendly message + retry action. Log technical details to console/monitoring.

### Patterns
- Use React `Suspense` boundaries with skeleton fallbacks for RSC.
- Use `ErrorBoundary` components to catch render errors gracefully.
- Wrap pages/features in `<ErrorBoundary fallback={<ErrorFallback />}>`.
- Toast notifications (via `sonner` or shadcn/ui toast) for non-blocking feedback.
- Full-page error screens for unrecoverable errors (500, offline).

---

## Critical Rules

1. Never use `any` in TypeScript. Use `unknown` with type narrowing.
2. Never use `useEffect` for data fetching. Use RSC, server actions, or TanStack Query.
3. Never use `<div onClick>`. Use `<button>` or `<a>` for interactive elements.
4. Never hardcode colors, spacing, or breakpoints. Use Tailwind design tokens.
5. Never ship UI without testing keyboard navigation and screen reader basics.
6. Every component must handle loading, error, empty, and success states.
7. Commit only after linting, type-checking, and tests pass.
