# Test Edge Diagnostics - 2025-10-28

## Log paths validated by tests

- PostgreSQLClient emits `Error storing analysis result` when the insert path surfaces a constraint violation, confirming the error channel is surfaced and the exception propagates.
- PostgreSQLClient debug message `Failed to decode features JSON` triggers when malformed feature payloads appear, ensuring downstream consumers still receive the raw text.
- E2B sandbox manager records `Created new E2B sandbox` and `Destroyed E2B sandbox` during the happy-path lifecycle, proving that pool activity metrics will be traceable in production logs.

## Diagnostics that still lack coverage

- DatadogClient success/error logging, including API key absence, HTTP error retries, and StatsD socket failures, is still untested; real log hooks remain unverified.
- E2B sandbox health-check degradations (`Sandbox ... health check failed`) and scale-down paths do not yet have assertions, leaving resilience alerts unvalidated.
- PostgreSQL connection bootstrap failures (`Failed to connect to database`) and compliance report degradation logs are not simulated, so observability for startup issues and SLA drops is uncertain.

## Follow-up actions

1. Introduce DatadogClient unit tests with stubbed transport to assert info/error logging on both metric and event publishing paths.
2. Add sandbox manager health-check simulations that drive degraded/dead states to verify warning logs and auto-destruction metrics.
3. Create PostgreSQLClient connection failure tests using a fake pool factory to confirm the critical `Failed to connect` log is raised and properly escalated.
