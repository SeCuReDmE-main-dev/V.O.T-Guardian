# Test Coverage Update (2025-10-28)

## Latest Regression Sweep

- `pytest --maxfail=5 --disable-warnings`
- Result: **39 passed / 4 skipped** spanning sandbox, Tenebris, Datadog, pipeline, ML, and persistence modules following the new sandbox recovery scenarios.

## Full Coverage Sweep

- `pytest --cov=src --cov-report=term-missing`
- Overall coverage: **71%** (339 misses / 1,161 statements).
- Key module snapshots:
  - `src/core/security/tenebris.py` **99%** (unchanged, line 270 branch outstanding).
  - `src/core/monitoring/datadog_client.py` **78%** with retry recovery paths now exercised end-to-end.
  - `src/core/e2b/sandbox_manager.py` **62%** including new recovery, quota, degradation, and pool exhaustion assertions.
  - `src/core/database/postgresql_client.py` **64%**; corruption/rollback cases remain pending fixtures.
- Warnings limited to known torch CUDA fallback and legacy async test placeholders (unchanged).

## Coverage Snapshot – 2025-10-28

| Module | Coverage | Notes |
| --- | --- | --- |
| API entrypoint (`src/api/main.py`) | 78% | Pending auth/token refresh branches and error handlers. |
| Settings (`src/config/settings.py`) | 77% | Gap on dynamic env fallback helpers. |
| Audio processor | 67% | Feature extraction error branches remain untested. |
| PostgreSQL client | 64% | Persistence retries/rollback flows still TODO. |
| Sandbox manager | 62% | Scale-in timers and long-running health loop still uncovered. |
| ML predictor | 60% | Drift detection, GPU inference, and alerting stubs. |
| Datadog client | 78% | Success-path + retry coverage validated after log-level fix. |

## Incremental Coverage Gains

- Sandbox manager suite rebuilt to exercise recovery success, retry exhaustion, quota errors, degraded health, and pool exhaustion logging.
- Datadog metric/event retry tests now assert both warning and info diagnostics, validating the success-path logging contract.
- Full suite run confirmed pipeline and persistence modules remain green after integrating the sandbox regression scenarios.

## Remaining Low-Coverage Focus

- `src/core/database/postgresql_client.py`: build corruption fixtures covering failover and rollback.
- `src/core/e2b/sandbox_manager.py`: add timer-driven health loop assertions and multi-template scaling cases.
- `src/core/ml/predictor.py`: flesh out drift monitoring and GPU inference fallbacks.
- `src/core/audio/processor.py`: extend to cover exception paths in denoise and feature transforms.

## Historical Baseline

- Previous aggregate run: coverage at **63%** (406 misses / 1,098 statements) before Datadog retry + sandbox recovery enhancements.
- Earlier focus areas covered Datadog failover telemetry, sandbox lifecycle happy path, and PostgreSQL compliance degradation handling.

## Next Steps

1. Exercise Tenebris violation handling under Datadog outage to close final 1% gap.
2. Extend sandbox manager tests for scheduled scale-in and long-lived pool drift.
3. Implement PostgreSQL corruption/rollback tests, then rerun coverage to quantify uplift toward PO3 readiness.
