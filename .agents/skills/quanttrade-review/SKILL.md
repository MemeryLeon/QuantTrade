---
name: quanttrade-review
description: Review a QuantTrade branch, commit, or pull request against main for scope, architecture, tests, data semantics, reproducibility, security, and trading risks. Use for pre-merge review or when asked to inspect changes. Do not implement unrelated features.
---

# QuantTrade Review

## Purpose
Review a QuantTrade change set before merge.

## Inputs
Determine whether the target is the working tree, current branch versus `main`, a commit range, or a PR. Read `AGENTS.md`, `PROJECT_PLAN.md`, `TASKS/INDEX.md`, the current stage task file, and relevant ADRs.

## Review order

### 1. Scope
- Implements only the current branch task package.
- No future-stage tables, modules, pages, or placeholders.
- No unrelated refactors.

### 2. Architecture
Verify `API → Application → Domain ← Infrastructure`.
Block if Router accesses infrastructure directly, Domain imports frameworks, React components bypass generated clients, LEAN raw structures leak, or long tasks use FastAPI BackgroundTasks.

### 3. Contracts and migrations
- Explicit Pydantic models.
- No bare `dict`, `Any`, or `list[dict]` in core contracts.
- Reversible migrations limited to the current stage.
- Breaking API changes approved.
- OpenAPI frontend types synchronized.

### 4. Data safety
Check timezone-aware datetimes, source, adjustment, calendar, freshness, quality flags, snapshot integrity, no silent fills, no stale data in formal workflows, and no look-ahead data. Use `$quanttrade-data-safety` for data-sensitive changes.

### 5. Backtest reproducibility
Verify source identity, strategy digest, data snapshot, LEAN digest, parser version and digest, raw schema, fixture, fees, slippage, compatibility tests, and Golden Fixture.

### 6. Broker and trading safety
Verify typed BrokerStateResult, fail-closed stale state, idempotency, RiskService order, reconciliation, Kill Switch, and no Live bypass.

### 7. Tests and operations
Check unit, contract, integration, E2E, `make check`, secret-safe logs, observability, and rollback.

## Severity
- **BLOCKER**: corrupts data, invalidates backtests, duplicates orders, bypasses risk, leaks secrets, or violates a hard rule.
- **MAJOR**: contract, migration, scope, test, or reproducibility defect.
- **MINOR**: limited maintainability or clarity issue.
- **NOTE**: optional improvement.

## Output
List findings first, ordered by severity. Include file/symbol, exact problem, consequence, and minimal correction. Then list tests, assumptions, and merge recommendation: `BLOCK`, `APPROVE AFTER FIXES`, or `APPROVE`.
