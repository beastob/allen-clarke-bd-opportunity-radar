---
name: implement
description: "Implement a piece of work based on a spec or set of tickets, isolated in a git worktree and merged back to the local branch on completion."
disable-model-invocation: true
---

# Implementation Protocol

Execute work through strict phase gates. Each phase is a hard boundary with a checkable completion criterion. All work happens in an isolated git worktree; the local branch stays untouched until Phase 4.

## Phase 0: Isolate in a worktree

1. **Capture context**: From the ticket, get the issue number and a short slug. Capture the merge target: the branch the main repo is on at invocation (`git branch --show-current`).
2. **Create the worktree**: `git worktree add -b issue/<n>-<slug> ../<repo>-worktrees/<n>-<slug> <target>` (`<repo>` = the repo directory's name). If the branch already exists (resuming), drop `-b`: `git worktree add issue/<n>-<slug> ../<repo>-worktrees/<n>-<slug>`.
3. **Install dependencies** in the worktree (`npm install`).
4. **Operate inside the worktree from here on.** Every command in Phases 1-4 runs with the worktree as the working directory. Any sub-agent you spawn receives the worktree path and instructions to work there.

**Gate Criterion**: `git worktree list` shows the new worktree on branch `issue/<n>-<slug>`, dependencies installed, and you are operating inside it.

## Phase 1: Seam Agreement & TDD Setup
*Pointer*: Read [.agents/skills/tdd/SKILL.md] before starting.

1. **Identify Seams**: Define public interface seams under test and record them in `implementation_plan.md` under Proposed Changes. Commit `implementation_plan.md` in the worktree branch so it travels through the merge.
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

1. **Spawn Parallel Reviewers**: Execute 2-axis review (Standards & Spec) by launching parallel sub-agents. Diff fixed point: `git diff <target>...HEAD` run in the worktree; pass each sub-agent the worktree path so they diff and read from there.
2. **Record Findings**: Report review findings in `walkthrough.md` or execution summary.
3. **Resolve Blockers**: Fix all hard violations or blocker findings identified by either reviewer.

**Gate Criterion**: Parallel `/code-review` sub-agents have executed against `git diff <target>...HEAD` in the worktree and all blocker findings are resolved.

## Phase 4: Merge Back & Clean Up
1. **Commit**: Stage changes and commit in the worktree branch using a recognized GitHub closing keyword referencing the issue.
2. **Sync before merging**: `git fetch origin`, then rebase the worktree branch onto `origin/<target>`. Resolve conflicts in the worktree. If anything changed, re-run the Phase 2 gate.
3. **Merge serially into the local branch**: In the main repo, `git checkout <target>` then `git merge --no-ff issue/<n>-<slug>`. Only one merge at a time: if the target advanced since your rebase, re-sync and retry.
4. **Push**: If the target is the repository's default branch, push it directly; otherwise push to origin and open/merge a PR into the default branch.
5. **Close the issue**: `gh issue close <n> --comment "<one-line summary; merged to <target> in <merge-sha>"`. The closing keyword only auto-closes once the commit reaches the default branch — when the merge target isn't the default branch, close it explicitly so it doesn't linger open.
6. **Clean up**: `git worktree remove ../<repo>-worktrees/<n>-<slug> --force`, `git worktree prune`, `git branch -d issue/<n>-<slug>`.

**Gate Criterion**: The merge commit is visible on the local target branch (`git log --oneline -1`), pushed, the issue closed on GitHub, and the worktree removed.
