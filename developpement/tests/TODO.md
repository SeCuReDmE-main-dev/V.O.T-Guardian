# Test TODOs

## Completed

- [x] Add unit tests for `MLPredictor.predict` in `src/core/ml/predictor.py`, mocking Torch tensors to verify probability normalization, confidence threshold enforcement, and fallback behavior when the model reports low confidence.

## Critical (P0)

- [x] Hard-test `DatadogClient` failover: cover missing API key, HTTP error retries, and StatsD socket failures with log assertions (complete).
- [x] Validate Datadog success-path telemetry so healthy traffic remains observable.
- [ ] Capture Datadog retry/backoff diagnostics once the scheduler is implemented.

## High (P1)

- [x] Simulate E2B sandbox resource exhaustion to verify pool exhaustion errors and health-check downgrades (recovery paths pending).
- [ ] Extend E2B coverage to recovery and scale-in operations with audit logging.
- [ ] Validate PostgreSQL persistence against malformed payloads and row-level corruption, confirming audit/compliance diagnostics stay accurate under partial failures.
- [ ] Add Tenebris key rotation and manual override scenarios to prove security fallbacks stay observable.

## Medium (P2)

- [ ] Exercise API throttling and Tenebris policy reload fallbacks to ensure security monitoring logs surface degraded states without breaking analysis requests.
