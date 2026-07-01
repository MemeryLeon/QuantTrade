---
name: ibkr-risk-gate
description: Audit QuantTrade IBKR Paper or Live order execution, broker state, fail-closed behavior, idempotency, reconciliation, risk rules, and Kill Switch. Use explicitly for stages F and G or any broker/order change.
---

# IBKR Risk Gate

## Purpose
Prevent risk bypass, stale broker decisions, duplicate orders, and unapproved Live use.

## Broker state contract
`IBrokerGateway.get_state()` returns a typed result with status, state, as_of, error_code, error_message, and trace_id.
Allowed states: `AVAILABLE`, `STALE`, `UNAVAILABLE`, `RECONCILIATION_REQUIRED`.
Infrastructure converts expected disconnects, timeouts, rate limits, expired sessions, maintenance, and incomplete state into typed results. RiskService must not catch raw IBKR SDK network exceptions. Unexpected exceptions are logged at the Application boundary and fail closed.

## Freshness gate
State-dependent rules reject disconnected, stale, unavailable, unreconciled, missing-timestamp, or inconsistent state with:
`result=rejected`, `code=BROKER_STATE_UNKNOWN`.
Mandatory for Paper and Live.

## Order path
Require:
`Strategy Signal → TradeIntent → RiskCheck → Approval → BrokerOrder → OrderEvent → Fill → Reconciliation`.
Verify RiskService precedes submission, every order has an idempotency key, retries cannot duplicate orders, broker truth wins, late events are deterministic, and differences are not silently corrected.

## Kill Switch
Verify cross-process state, blocks new orders, does not hide open orders, is audited, survives restarts, and cannot be bypassed by Live.

## Paper observation
Before stage F completion require real data for at least 3 actual trading days:
- unresolved order/fill/position differences = 0;
- duplicate orders = 0;
- unresolved critical incidents = 0;
- Kill Switch drill passed;
- disconnect recovery drill passed.
Do not fabricate observation time or reports.

## Output
Return blocking findings, broker contract status, idempotency, reconciliation, Kill Switch, observation status, and recommendation: `BLOCK`, `PAPER_ONLY`, or `READY_FOR_HUMAN_GATE`. Never recommend automatic Live activation.
