# Test Edge Diagnostics - 2025-10-28

## Log paths validated by tests

- PostgreSQLClient emits `Error storing analysis result` when the insert path surfaces a constraint violation, confirming the error channel is surfaced and the exception propagates.
- PostgreSQLClient debug message `Failed to decode features JSON` triggers when malformed feature payloads appear, ensuring downstream consumers still receive the raw text.
- E2B sandbox manager records `Created new E2B sandbox`, `Destroyed E2B sandbox`, and degraded health logs (`Sandbox ... response degraded`) confirming pool lifecycle and health regressions are traceable.
- DatadogClient now surfaces `Datadog failover - ...` diagnostics for outages and emits success logs (`Datadog metric recorded`, `Datadog event published`) when telemetry flows normally.
- Tenebris protocol audits capture `TENEBRIS_START`, `TENEBRIS_PURGE_COMPLETE`, and violation entries with resilient fallbacks when Datadog auditing fails.

## Diagnostics that still lack coverage

- DatadogClient still lacks multi-region retry backoff visibility and success metrics for long-running batch telemetry. *(reportée)*
- E2B sandbox manager does not yet simulate hard health-check failures or auto-scaling shrink events beyond warning logs. *(à planifier)*
- PostgreSQL connection bootstrap failures (`Failed to connect to database`) and compliance report degradation logs are not simulated, so observability for startup issues and SLA drops is uncertain. *(à planifier)*
- Tenebris lacks regression tests for key rotation latency and manual override flows. *(à planifier)*

## Follow-up actions

1. Capture Datadog retry scheduling metadata and long-running telemetry batching once implemented. *(reportée)*
2. Simulate E2B sandbox hard failures and scale-in decisions to validate automatic destruction and recovery paths. *(à planifier)*
3. Create PostgreSQLClient connection failure tests using a fake pool factory to confirm the critical `Failed to connect` log is raised and properly escalated. *(à planifier)*
4. Add Tenebris key rotation and override scenario coverage to assure security fallbacks stay observable. *(à planifier)*
