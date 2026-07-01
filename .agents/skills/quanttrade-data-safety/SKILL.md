---
name: quanttrade-data-safety
description: Audit QuantTrade market data, snapshots, adjustments, calendars, time semantics, quality flags, Parquet schemas, stale-cache rules, and look-ahead prevention. Use for stages C, D, H, and I or any data-sensitive implementation.
---

# QuantTrade Data Safety

## Purpose
Prevent incorrect market data, ambiguous time semantics, non-reproducible snapshots, and look-ahead bias.

## Provider result
Require instrument, provider, market, currency, resolution, adjustment, timezone, `as_of`, `is_delayed`, and `quality_flags`.

## Health and degradation
Validate `healthy`, `degraded`, `unavailable`, and `recovering`.
For stale display cache require `is_delayed=true`, actual `as_of`, `stale_age_seconds`, `STALE_CACHE`, and `PROVIDER_DEGRADED`.
Stale cache must not create formal snapshots, LEAN backtests, risk states, or order decisions.

## Time semantics
Identify observation time, publication time, system availability time, and strategy effective time. Reject timezone-naive datetimes. Factors and ML may use only data available by the decision timestamp.

## Snapshot integrity
`data_snapshots` stores metadata only; large data belongs in MinIO. Verify URI, checksum, row count, schema, calendar, adjustment, time range, timezone, and provider. Redis is not the reproducibility source.

## Parquet
PyArrow is the only implementation. Test timezone timestamps, price precision, integer volume, nulls, column types, and schema version.

## Adjustments
Verify explicit raw/adjusted prices, snapshotted factors, recovery without Redis, deterministic calculation, and `ADJUSTMENT_FACTOR_MISSING` on missing factors.

## Calendar
Check version, holidays, half-days if supported, cross-year boundaries, and mismatch flags. Do not use an implicit weekday-only calendar.

## Quality flags
At minimum detect:
`MISSING_BARS`, `DUPLICATE_BARS`, `OUT_OF_ORDER`, `STALE_CACHE`, `PROVIDER_DEGRADED`, `PROVIDER_UNAVAILABLE`, `ADJUSTMENT_FACTOR_MISSING`, `CALENDAR_MISMATCH`, `TIMEZONE_AMBIGUOUS`.
Never silently fill missing bars.

## Output
Return blocking defects, ambiguous definitions requiring user decision, missing tests, reproducibility impact, and exact acceptance tests.
