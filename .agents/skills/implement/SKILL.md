---
name: implement
description: "Implement a piece of work based on a spec or set of tickets directly on the main branch."
disable-model-invocation: true
---

# Implementation Protocol

Execute work through strict phase gates. Each phase is a hard boundary with a checkable completion criterion. All work happens directly on the `main` branch.

## Phase 0: Context & Workspace Sync

1. **Capture context**: From the ticket or spec, get the issue number, title, and acceptance criteria.
2. **Sync main branch**: Ensure you are on the `main` branch (`git checkout main`), the working tree is clean, and pull the latest changes (`git pull origin main`).
3. **Install dependencies**: Ensure dependencies are up to date (`npm install` or repo-appropriate package manager).

**Gate Criterion**: Operating on `main` branch, workspace is synced and clean, and dependencies are installed.

## Phase 1: Seam Agreement & TDD Setup
*Pointer*: Read [.agents/skills/tdd/SKILL.md] before starting.

1. **Identify Seams**: Define public interface seams under test and record them in `implementation_plan.md` under Proposed Changes.
2. **User Confirmation**: Confirm agreed test seams with the user before writing implementation code.
3. **Red-Green Loop**: Execute vertical slice red → green cycles per seam (failing test first, minimal code to pass).

**Gate Criterion**: All pre-agreed seams have passing unit/integration tests written test-first.

## Phase 2: Verification Loop
1. Run typechecking against modified files (the repo's own typecheck command).
2. Run targeted test files during development.
3. Run the repo's full test command to verify all tests pass cleanly.

**Gate Criterion**: Full test suite passes clean with zero typechecking or test failures.

## Phase 3: Review Gate
*Pointer*: Read [.agents/skills/code-review/SKILL.md] before executing review.

1. **Spawn Parallel Reviewers**: Execute 2-axis review (Standards & Spec) by launching parallel sub-agents. Diff fixed point: compare against `origin/main` or the initial commit before changes (`git diff origin/main...HEAD` or working tree diff).
2. **Record Findings**: Report review findings in `walkthrough.md` or execution summary.
3. **Resolve Blockers**: Fix all hard violations or blocker findings identified by either reviewer.

**Gate Criterion**: Parallel `/code-review` sub-agents have executed and all blocker findings are resolved.

## Phase 4: Commit, Push & Close Issue
1. **Commit**: Stage changes and commit directly on `main` using a recognized GitHub closing keyword referencing the issue (e.g., `Closes #<n> <summary>`).
2. **Sync before pushing**: Run `git pull --rebase origin main` to incorporate any new remote changes. If anything changed or conflicts were resolved, re-run the Phase 2 gate.
3. **Push**: Push commits directly to `origin main` (`git push origin main`).
4. **Close the issue**: `gh issue close <n> --comment "<one-line summary; committed to main in <sha>"`.
5. **Clean up**: Remove any temporary scratch or test artifacts.

**Gate Criterion**: Changes are committed and pushed to `main` on origin (`git log --oneline -1`), and the issue is closed on GitHub.
