# PostgreSQL Teardown & Retry Observability — 2025-10-29

## Overview
- Added dedicated tests exercising `_close_pool_with_metrics` under maintenance and saturation scenarios.
- Verified retry protocol during partial migration failures and pool exhaustion with deterministic logging.
- Confirmed disconnect path delegates to teardown instrumentation and leaves pools in a closed, observable state.

## Observability Samples
```
INFO src.core.database.postgresql_client:PostgreSQL pool teardown (maintenance-window): duration=0.1250s connections=4 memory_before=4096 memory_after=1024
INFO src.core.database.postgresql_client:PostgreSQL pool teardown (saturation-recovery): duration=0.0320s connections=7 memory_before=n/a memory_after=n/a
WARNING src.core.database.postgresql_client:Database initialization failed, rolling back pending migrations: migration step 3/5 crashed
INFO src.core.database.postgresql_client:Database connection attempt 1/2 failed: pool exhausted
```

## Validated Corner Cases
- Maintenance window teardown captures duration, live connection count, and traced memory deltas.
- Saturation recovery falls back to holder-count estimation when the pool lacks explicit counters.
- Partial migration rollback records both `init-failure` and `failure` teardown reasons and retries successfully on the next pool.
- Connection exhaustion surfaces retry logging while preserving the healthy pool once resources become available.
- `disconnect()` funnels through the metrics path, guaranteeing observability even on manual shutdown.

## Points d'amélioration
1. Add integration coverage for telemetry export (Datadog) to confirm teardown metrics are forwarded beyond logging.
2. Exercise idle teardown when no pool has ever been established to ensure `disconnect()` stays silent and fast.
3. Capture negative-path memory sampling when `tracemalloc` tracing stops mid-operation, ensuring we continue to log gracefully.
