---
name: quanttrade-task-runner
description: Execute one QuantTrade READY branch task package using the repository task index, tests, commits, PR gate, and user acceptance workflow. Use only when explicitly invoked to start or continue a QuantTrade task package. Do not use for ordinary coding questions or ad-hoc edits.
---

# QuantTrade Task Runner

## Purpose
Execute exactly one branch task package from the QuantTrade Loop Engineering workflow.

## Required inputs
Read, in order:
1. `AGENTS.md`
2. `PROJECT_PLAN.md`
3. `TASKS/INDEX.md`
4. The current stage file under `TASKS/`
5. Relevant code, tests, ADRs, design reviews, and acceptance records

If any required file is missing, stop and report the missing path. Do not invent a replacement workflow.

## Select the task package
1. Find the first task package whose status is `READY`.
2. Confirm all listed dependencies are `DONE`.
3. Confirm no other task package is active unless the user explicitly approved parallel work.
4. Use only the branch name written in the stage task file.
5. Do not skip ahead.

## Start the branch
```bash
git switch main
git pull
git status
git switch -c <task-package-branch>
```

Requirements:
- `main` must be clean before creating the branch.
- Do not use `git reset --hard`, `git clean -fd`, force push, or destructive history edits.
- If the branch already exists, inspect it before switching. Do not overwrite it.

## Work loop
For each numbered task in the branch package:
1. Mark the task `DOING`.
2. Inspect existing implementation and tests.
3. State a short implementation plan.
4. Implement only the written scope.
5. Run task-specific tests.
6. Fix all failures.
7. Review relevant architecture, data semantics, time zones, security, and error handling.
8. Update documentation.
9. Mark the task `DONE`.
10. Create one clear commit for that numbered task.

Do not create a new branch or PR for each numbered task.

## Design and risk gates
Stop before continuing when the task requires architecture, migration, API, data, LEAN, IBKR, risk, or Live approval.

For `B-BR1`, complete B0/B1 and `docs/architecture/B_CORE_DESIGN_REVIEW.md`, then stop until the user approves.

## Complete the branch package
Run:
```bash
make check
```
When applicable also run:
```bash
make test-integration
make e2e
```

Then review the full diff, confirm scope, update task status, push the branch, and create one PR. If CI fails, continue fixing on the same branch.

## Merge and acceptance
- Never merge a high-risk package without explicit user approval.
- After merge, set status to `USER_ACCEPTANCE` and stop.
- Only after the user says `验收通过，继续` may the package be marked `DONE` and the next eligible package become `READY`.
- Do not treat silence or elapsed time as acceptance.

## Output
Report:
- task package and branch;
- completed tasks;
- tests and results;
- commits;
- current status;
- required human decision;
- next permitted action.
