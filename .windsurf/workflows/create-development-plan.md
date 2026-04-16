---
description: Create an agile development plan structured by releases, sprints, and tasks. Each task enforces a strict develop → test → commit cycle.
---
# Create Development Plan Workflow

## Prerequisites
- Product requirements, user story, or feature request is provided.
- Project tech stack and constraints are known (check `model-context.md`).

## Steps

### 1. Analyze Requirements
- Read the provided product requirements or user request thoroughly.
- Identify **functional requirements** (what the system must do).
- Identify **non-functional requirements** (performance, security, accessibility, i18n).
- Clarify ambiguities with the user before proceeding. List assumptions explicitly.
- Check `model-context.md` for existing constraints, conventions, and technical debt that may affect the plan.

### 2. Define Scope & Releases
- Break the overall goal into **releases** (deployable increments of value).
- Each release should be independently shippable and provide measurable user value.
- Order releases by dependency and business priority.

```markdown
## Release Plan
### Release 1.0 — <Title> (MVP)
- **Goal:** <what users can do after this release>
- **Target:** Sprint 1–3

### Release 1.1 — <Title> (Enhancement)
- **Goal:** <incremental improvement>
- **Target:** Sprint 4–5
```

### 3. Break Releases into Sprints
- Each sprint is **1–2 weeks** of work.
- Sprint goal: a coherent, testable slice of functionality.
- Order tasks within each sprint by dependency (database → backend → frontend → docs).

### 4. Define Tasks with Dev → Test → Commit Cycle
For **each task**, define the following strict sequence:

```markdown
#### Task X.Y: <Descriptive Title>
**Skill:** `@frontend-development` | `@backend-development` | `@database-management` | `@security-hardening`
**Priority:** High | Medium | Low
**Estimated effort:** S (< 2h) | M (2–4h) | L (4–8h) | XL (> 8h)

**Acceptance Criteria:**
- [ ] <specific, testable criterion 1>
- [ ] <specific, testable criterion 2>

**Implementation Steps:**
1. **Develop:** <what to build, which files to create/modify>
2. **Test:** <what tests to write — unit, integration, or E2E>
3. **Verify:** Run test suite locally — all tests must pass
4. **Commit:** `<type>(<scope>): <description>` (Conventional Commits)

**Dependencies:** Task X.Z (if any)
```

### 5. Structure the Plan as a Trackable Checklist
Output the finalized plan in this format:

```markdown
# Development Plan — <Project/Feature Name>

**Created:** YYYY-MM-DD
**Last Updated:** YYYY-MM-DD
**Status:** Draft | In Progress | Complete

---

## Release 1.0 — <Title>

### Sprint 1 — <Sprint Goal>

- [ ] **Task 1.1:** <Title> (`@database-management`)
  - [ ] Develop: <description>
  - [ ] Test: <test description>
  - [ ] Verify: All tests pass
  - [ ] Commit: `feat(db): <message>`

- [ ] **Task 1.2:** <Title> (`@backend-development`)
  - [ ] Develop: <description>
  - [ ] Test: <test description>
  - [ ] Verify: All tests pass
  - [ ] Commit: `feat(api): <message>`

- [ ] **Task 1.3:** <Title> (`@frontend-development`)
  - [ ] Develop: <description>
  - [ ] Test: <test description>
  - [ ] Verify: All tests pass
  - [ ] Commit: `feat(ui): <message>`

- [ ] **Task 1.4:** Documentation (`@documentation-writer`)
  - [ ] Update API docs
  - [ ] Update user manual
  - [ ] Update `model-context.md`
  - [ ] Commit: `docs: <message>`

### Sprint 2 — <Sprint Goal>
...

---

## Release 1.1 — <Title>
...
```

### 6. Validate the Plan
Before presenting to the user, verify:
- [ ] Every task has clear acceptance criteria.
- [ ] Every task follows the develop → test → commit cycle.
- [ ] Dependencies between tasks are explicit and acyclic.
- [ ] Each sprint ends with a testable, demonstrable increment.
- [ ] Documentation tasks are included (not deferred to "later").
- [ ] Security considerations are addressed (invoke `@security-hardening` for auth/data tasks).
- [ ] Accessibility requirements are included in frontend tasks.
- [ ] The plan references the correct skills for each task type.

### 7. Present & Iterate
- Present the plan to the user for review.
- Incorporate feedback and adjust sprint assignments, priorities, or scope.
- Save the final plan to `docs/plans/<feature-name>-plan.md` for tracking.
