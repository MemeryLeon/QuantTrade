---
name: lean-compatibility
description: Validate QuantTrade LEAN runtime, parser compatibility, source identity, artifacts, schema compatibility, and Golden Fixtures. Use explicitly for stage D, LEAN upgrades, parser changes, or backtest reproducibility audits.
---

# LEAN Compatibility

## Purpose
Determine whether the LEAN backtest path is compatible and reproducible.

## Read
Read `PROJECT_PLAN.md`, `lean/compatibility/manifest.yaml`, Docker config, Parser code, Golden Fixtures, source identity implementation, task files, and CI.

## Compatibility tuple
Require a registered tuple:
`lean_image_digest`, `parser_version`, `parser_artifact_digest`, `raw_output_schema_version`, `fixture_version`.
Verify the actual Parser Artifact Digest; do not trust an edited value without comparison.

## Version semantics
- LEAN raw structure changed → increment Raw Output Schema Version.
- Parser code changed → Parser Artifact Digest must change.
- Parsed behavior or expected result changed → assess and normally increment Fixture Version.
- Do not increment Raw Schema merely because Parser code changed.

## Source identity
Local formal backtests require `git_workspace_clean=true`, `platform_git_sha`, and `platform_source_tree_digest`. Reject dirty workspaces with `WORKSPACE_DIRTY`.
Immutable deployments require `backend_image_digest`, `build_git_sha`, `platform_source_tree_digest`, and `source_identity_mode=immutable_build`. Reject missing identity with `SOURCE_IDENTITY_UNAVAILABLE`.
Mock backtests may run dirty but cannot be labeled formal LEAN results.

## Runtime isolation
Verify dedicated queue, concurrency=1, prefetch=1, one slot per container, CPU/memory/time/output/queue limits, and cleanup after all outcomes.

## Tests
Require engine contract tests, Schema Compatibility Test, Golden Fixture, malformed output, timeout/cancel, invalid snapshot, source identity, and cleanup tests.

## Result
Return `COMPATIBLE`, `INCOMPATIBLE`, `NOT_REPRODUCIBLE`, or `NEEDS_HUMAN_DECISION`, with exact blockers. Never edit the manifest merely to make a failure pass.
