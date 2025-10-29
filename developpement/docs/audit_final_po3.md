# Audit final PO3 — PostgreSQL Client

## Synthèse rapide
- Teardown metrics instrumented and verified under maintenance and saturation paths.
- Retry/rollback flow validated for partial migrations and pool exhaustion scenarios.
- Disconnect pathway confirmed to funnel through metrics, preventing silent pool shutdowns.

## Matrice de tests exécutés
- `test_close_pool_with_metrics_emits_observability_logs`
- `test_close_pool_with_metrics_estimates_holder_count`
- `test_disconnect_invokes_teardown_metrics`
- `test_connect_partial_migration_failure_rolls_back`
- `test_connect_pool_exhaustion_recovers`
- Legacy regression suite (12 existing cases) covering compliance, corruption, retries, and init failures.

## Couverture ciblée
- Commande: `python -m coverage run -m pytest tests/test_postgresql_client.py`
- Rapport: `python -m coverage report src/core/database/postgresql_client.py`
- Résultat: **83%** (174 statements / 29 misses) sur `src/core/database/postgresql_client.py`.

## Extraits de logs observés
```text
INFO src.core.database.postgresql_client:PostgreSQL pool teardown (maintenance-window): duration=0.1250s connections=4 memory_before=4096 memory_after=1024
INFO src.core.database.postgresql_client:PostgreSQL pool teardown (saturation-recovery): duration=0.0320s connections=7 memory_before=n/a memory_after=n/a
WARNING src.core.database.postgresql_client:Database initialization failed, rolling back pending migrations: migration step 3/5 crashed
INFO src.core.database.postgresql_client:Database connection attempt 1/2 failed: pool exhausted
```

## Problèmes corrigés
- Teardown instrumentation now consistently logs memory samples and connection estimates.
- Partial migration failures close pools via metrics before retrying, preventing leaked connections.
- Pool exhaustion produces structured retries without tearing down the succeeding pool.

## Points ouverts
1. Export teardown metrics to Datadog (currently log-only).
2. Cover idle disconnect when no pool was created to ensure silent noop behaviour.
3. Exercise failure paths where `tracemalloc` tracing stops mid-teardown.
