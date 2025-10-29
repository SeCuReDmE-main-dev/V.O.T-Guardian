# Test TODOs

## Completed

- [x] Add unit tests for `MLPredictor.predict` in `src/core/ml/predictor.py`, mocking Torch tensors to verify probability normalization, confidence threshold enforcement, and fallback behavior when the model reports low confidence.

## Critical (P0)

- [ ] Hard-test `DatadogClient` failover: cover missing API key, HTTP error retries, and StatsD socket failures with log assertions (next micro-task).

## High (P1)

- [ ] Simulate E2B sandbox resource exhaustion to verify pool exhaustion errors, health-check downgrades, and auto-scaling recovery logging.
- [ ] Validate PostgreSQL persistence against malformed payloads and row-level corruption, confirming audit/compliance diagnostics stay accurate under partial failures.

## Medium (P2)

- [ ] Exercise API throttling and Tenebris policy reload fallbacks to ensure security monitoring logs surface degraded states without breaking analysis requests.
