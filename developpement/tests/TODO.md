# Test TODOs

## Completed

- [x] Add unit tests for `MLPredictor.predict` in `src/core/ml/predictor.py`, mocking Torch tensors to verify probability normalization, confidence threshold enforcement, and fallback behavior when the model reports low confidence.
- [x] Validate Tenebris destruction failure reporting (sandbox reuse and unauthorized key revocation) to unblock PO3 security gating.

## Critical (P0)

- [x] Hard-test `DatadogClient` failover: cover missing API key, HTTP error retries, and StatsD socket failures with log assertions (complete).
- [x] Validate Datadog success-path telemetry so healthy traffic remains observable.
- [ ] Capture Datadog retry/backoff diagnostics once the scheduler is implemented.
- [ ] Exercise Datadog transport recovery chain under forced outage to close remaining Tenebris violation coverage gap.

## High (P1)

- [x] Simulate E2B sandbox resource exhaustion to verify pool exhaustion errors and health-check downgrades (recovery paths pending).
- [ ] Extend E2B coverage to recovery and scale-in operations with audit logging (micro-test gating for PO3).
- [ ] Validate PostgreSQL persistence against malformed payloads and row-level corruption, confirming audit/compliance diagnostics stay accurate under partial failures.
- [ ] Add Tenebris key rotation and manual override scenarios to prove security fallbacks stay observable (violation groundwork complete, rotation pending).
- [ ] Capture persistence edge diagnostics (backup replica lag, failover) to ensure observability chain recovers cleanly.

## Medium (P2)

- [ ] Exercise API throttling and Tenebris policy reload fallbacks to ensure security monitoring logs surface degraded states without breaking analysis requests.

## Notes

- Progress toward PO3: Tenebris violation coverage landed; remaining blockers are Datadog retry telemetry, sandbox recovery heuristics, and persistence corruption drills.
