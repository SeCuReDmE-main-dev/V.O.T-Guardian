# Test Coverage Update (2025-10-28)

## Latest Targeted Regression

- `python -m pytest tests/test_tenebris.py tests/test_e2b_sandbox_manager.py tests/test_datadog_client.py`
- Result: 15 tests passed (Tenebris 5, sandbox manager 4, Datadog telemetry 6) validating cleanup changes against monitoring and sandbox integrations.
- Focus: ensure Tenebris metadata purges do not regress Datadog success-path telemetry or sandbox lifecycle flows.

## Full Coverage Sweep

- `python -m pytest --cov=src --cov-report=term-missing`
- Overall coverage: **70%** (339 misses / 1119 statements).
- `src/core/security/tenebris.py` now reports **99%** coverage with only the aggregation branch at line 270 outstanding.
- No regressions detected across Datadog telemetry or E2B sandbox suites during the sweep (32 passed / 4 skipped).

## Incremental Coverage Gains

- Tenebris cleanup path now executes with and without encryption, covering key revocation, memory scrubbing, and compliance report reporting.
- Violation paths now simulate destroyed sandbox retries and unauthorized key revocation, asserting Datadog `TENEBRIS_DESTRUCTION_FAILED` diagnostics and logger output.
- Datadog client success-path telemetry remains stable under recorder stubs; targeted rerun confirmed no regressions post-cleanup.
- E2B sandbox manager degradation/exhaustion scenarios rerun to confirm compatibility with the Tenebris session lifecycle adjustments.

## Remaining Low-Coverage Modules

- `src/core/database/postgresql_client.py`: deeper persistence retries and compliance report degradations remain open.
- `src/core/e2b/sandbox_manager.py`: scaling heuristics and long-lived pool recoveries still lack coverage beyond targeted assertions.
- `src/core/ml/predictor.py`: GPU and drift detection paths require dedicated fixtures.
- `src/core/monitoring/datadog_client.py`: retry scheduler hooks and transport health checks remain partially covered.

## Historical Baseline

- Previous commands:
  - `PYTHONPATH=. pytest --maxfail=5 --disable-warnings`
  - `PYTHONPATH=. pytest --cov=src --cov-report=term-missing`
- Baseline coverage snapshot: 63% (406 lines uncovered of 1098).
- Earlier targets included Datadog failover telemetry, sandbox lifecycle happy path, and PostgreSQL compliance degradation handling.

## Next Steps

1. Exercise Tenebris violation handling under Datadog outage to capture escalation branches (remaining 1% gap).
2. Expand sandbox manager tests for scale-in heuristics and timer-driven health refresh.
3. Refresh a full coverage run once Tenebris violation paths land to quantify the uplift and push toward PO3 readiness.
