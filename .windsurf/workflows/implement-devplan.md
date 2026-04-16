---
description: Given a development plan file, execute all tasks sequentially following the develop → test → commit cycle, updating checkboxes in the plan as each step completes.
---
# Implement Development Plan Workflow

## Prerequisites
- A development plan file is provided as argument (e.g., `docs/plans/all-features-plan.md`).
- The plan follows the structure from `/create-development-plan`: releases → sprints → tasks with `- [ ]` checkboxes.
- Development environment is set up and test suites are runnable (`cd backend && pytest`, `cd frontend && npm test`).
- `model-context.md` is available for project context.
- Git working tree is clean (no uncommitted changes).

## Inputs
- **Plan file**: The path to the development plan markdown file (provided via `@file` reference).

## Steps

### 1. Load and Parse the Plan
- Read the plan file in full.
- Read `model-context.md` for project context, conventions, and constraints.
- Identify the plan structure: releases, sprints, and tasks.
- Build a **task execution queue** by extracting all tasks in document order, preserving:
  - Task ID and title (e.g., "Task 1.1: Database connection pool configuration").
  - Skill tag (e.g., `@database-management`, `@backend-development`, `@frontend-development`, `@documentation-writer`).
  - Acceptance criteria (the `- [ ]` items under "Acceptance Criteria").
  - Implementation sub-steps (the `- [ ]` items under "Implementation Steps": Develop, Test, Verify, Commit).
  - Dependencies (other task IDs that must be completed first).
  - Priority and effort estimate.
- Count total tasks and present a summary to the user:

```
Plan: <plan title>
Releases: <count>
Sprints: <count>
Tasks: <count>
Estimated effort: <total>

Ready to begin with Sprint <first sprint>. Proceed?
```

- Wait for user confirmation before starting implementation.

### 2. Sprint-Level Execution Loop
For each sprint in the plan (in order):

1. **Announce the sprint:**
   ```
   --- Sprint <N>: <Sprint Goal> ---
   Tasks: <count in this sprint>
   ```

2. **Check dependencies:** For each task in the sprint, verify that all dependency tasks are already marked `[x]` in the plan file. If a dependency is unmet, flag it to the user and skip the task until resolved.

3. **Execute each task** in the sprint sequentially (see Step 3 below).

4. **Sprint checkpoint:** After all tasks in a sprint are complete, output a sprint summary:
   ```
   Sprint <N> complete: <completed>/<total> tasks done.
   ```

### 3. Task Execution Cycle (for each task)
Each task follows the strict **Develop → Test → Verify → Commit** cycle. Execute every sub-step under the task's "Implementation Steps" section.

#### 3a. Pre-Task
- Announce the task:
  ```
  Starting Task <ID>: <Title> [<Skill>] (<Effort>)
  ```
- Invoke the relevant skill based on the task's skill tag:
  - `@database-management` → invoke the `database-management` skill
  - `@backend-development` → invoke the `backend-development` skill
  - `@frontend-development` → invoke the `frontend-development` skill
  - `@security-hardening` → invoke the `security-hardening` skill
  - `@documentation-writer` → invoke the `documentation-writer` skill
- Read all files that will be modified (understand current state before editing).

#### 3b. Develop
- Execute the "Develop" sub-step described in the task.
- Create or modify the files listed in the implementation description.
- Follow project conventions from `model-context.md` and `.windsurf/rules/project_standards.md`:
  - Python: type hints, Pydantic v2, async/await, ruff formatting.
  - TypeScript: strict mode, no `any`, explicit return types.
  - React: functional components, Tailwind CSS, shadcn/ui, i18n keys.
  - SQL/Alembic: reversible migrations, proper constraints and indexes.
- After completing the develop sub-step, mark it in the plan file:
  ```
  - [x] Develop: <description>
  ```

#### 3c. Test
- Execute the "Test" sub-step described in the task.
- Write the tests specified (unit, integration, or E2E).
- Follow testing conventions:
  - Backend: pytest + pytest-asyncio, co-located test files in `tests/`.
  - Frontend: Vitest + Testing Library + MSW, co-located `.test.ts` files.
  - Test names: `it('should <behavior> when <condition>')` or `test_<behavior>_when_<condition>`.
- After writing tests, mark the sub-step in the plan file:
  ```
  - [x] Test: <description>
  ```

#### 3d. Verify
- Run the appropriate test suite to confirm all tests pass:
  - Backend tasks: `cd backend && pytest`
  - Frontend tasks: `cd frontend && npm test`
  - Database tasks: `cd backend && alembic upgrade head` (and optionally downgrade/upgrade)
  - Documentation tasks: no test run needed — verify files exist and are well-formed.
// turbo
- Run the test command and check the output.
- If tests **fail**:
  1. Read the error output carefully.
  2. Identify the root cause (in the new code, not the tests, unless the test is wrong).
  3. Fix the issue with a minimal upstream change.
  4. Re-run tests. Repeat up to 3 times.
  5. If still failing after 3 attempts, **stop and ask the user** for guidance. Do NOT mark the step as done.
- If tests **pass**, mark the sub-step in the plan file:
  ```
  - [x] Verify: All tests pass
  ```

#### 3e. Commit
- Stage all changed files related to this task.
- Commit using the exact commit message specified in the task's "Commit" sub-step.
- The commit message MUST follow Conventional Commits format: `<type>(<scope>): <description>`.
- After committing, mark the sub-step in the plan file:
  ```
  - [x] Commit: `<commit message>`
  ```

#### 3f. Post-Task
- After all sub-steps (Develop, Test, Verify, Commit) are marked `[x]`, mark the **parent task checkbox** as done:
  ```
  - [x] **Task <ID>:** <Title> (`<Skill>`)
  ```
- Also mark all acceptance criteria checkboxes for the task as done (if they were met during implementation):
  ```
  - [x] <acceptance criterion>
  ```
- Save the updated plan file after each task completes.
- Output a brief task completion message:
  ```
  ✓ Task <ID> complete. [<files changed> files, <tests added> tests]
  ```

### 4. Plan File Update Rules
The plan file is the **single source of truth** for progress. Follow these rules strictly:

- **Checkbox syntax:** Replace `- [ ]` with `- [x]` for completed items. Never alter any other text on the line.
- **Update timing:** Update the plan file immediately after each sub-step completes (not batched).
- **Update the plan status:** When the first task begins, change the plan header status from `Draft` to `In Progress`:
  ```
  **Status:** In Progress
  ```
- **Update the Last Updated date** at the top of the plan to today's date.
- **Never delete or rewrite** task descriptions, acceptance criteria, or implementation steps. Only toggle checkboxes.
- **If a task is skipped** (e.g., blocked by unresolved dependency), add a note below the task:
  ```
  > ⚠️ SKIPPED: Blocked by Task <X.Y> (not yet completed).
  ```

### 5. Error Handling & Recovery
- **Test failure:** Follow the retry logic in Step 3d (up to 3 attempts, then ask user).
- **Dependency not met:** Skip the task, log a warning, continue with the next independent task in the sprint. Revisit skipped tasks at the end of the sprint.
- **File conflict:** If a file was modified outside this workflow (detected via git status), alert the user before overwriting.
- **Ambiguous task:** If a task description is too vague to implement confidently, ask the user for clarification before proceeding. Do NOT guess.
- **Large task (XL):** For tasks estimated as XL (> 8h), break them into smaller logical chunks. Implement and commit each chunk separately, but only mark the parent task as done when all chunks pass.

### 6. Session Boundary Handling
If the workflow cannot complete all tasks in a single session:

- Ensure the plan file is saved with all current progress (checkboxes updated).
- Output a **progress summary**:
  ```
  Session paused after Task <ID>.
  Progress: <completed>/<total> tasks done.
  Next task: Task <next ID> — <Title>
  Current sprint: Sprint <N>
  
  Resume by running: /implement-devplan @<plan-file>
  ```
- On resume, the workflow re-reads the plan file, detects which tasks are already `[x]`, and continues from the first unchecked task.

### 7. Release Completion
When all tasks in a release are marked `[x]`:

1. Output a release summary:
   ```
   === Release <version> Complete ===
   Sprints: <count>
   Tasks completed: <count>
   Commits: <list of commit messages>
   Files changed: <total count>
   Tests added: <total count>
   ```

2. Run the full test suite one final time (backend + frontend) to confirm nothing regressed:
// turbo
   - `cd backend && pytest`
// turbo
   - `cd frontend && npm test`

3. If all pass, confirm the release is ready:
   ```
   Release <version> verified. All tests pass.
   ```

4. Ask the user if they want to continue with the next release or stop.

### 8. Plan Completion
When ALL tasks across ALL releases are marked `[x]`:

1. Change the plan status to `Complete`:
   ```
   **Status:** Complete
   ```

2. Output the final summary:
   ```
   === Development Plan Complete ===
   
   Releases delivered: <count>
   Total sprints: <count>
   Total tasks: <count>
   Total commits: <count>
   Total files changed: <count>
   Total tests added: <count>
   
   Documentation updated:
   - <list of doc files>
   
   model-context.md: Updated
   ```

3. Invoke the `@documentation-writer` skill to perform a final update of `model-context.md` with all new architecture, features, and decisions introduced during the plan execution.
