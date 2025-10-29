# E2B Sandbox Manager Test Report (2025-10-28)

## Test Matrix

- `test_sandbox_lifecycle_happy_path`: validates pool bootstrap, allocation context manager, stats counters, and teardown cleanup.
- `test_sandbox_creation_transient_failure_recovers`: simulates two transient `RuntimeError` failures before succeeding on the third attempt, asserting retry logging and stats counters.
- `test_sandbox_creation_retry_exhaustion_logs_error`: forces hard failures to ensure retry exhaustion and error logging propagate.
- `test_dead_sandbox_replaced_during_scale`: confirms dead entries are destroyed and replaced during `_scale_pool` execution.
- `test_sandbox_creation_quota_error`: verifies quota exceptions bubble up while emitting failure diagnostics and leaving the pool empty.
- `test_health_check_marks_degraded_and_logs`: exercises the health check loop, marking slow responders as degraded and updating aggregate stats.
- `test_acquire_sandbox_logs_pool_exhaustion`: confirms pool exhaustion surfaces as an exception with error-level telemetry.
- `test_scale_pool_trims_idle_sandboxes`: validates the automatic scale-in heuristic trims idle workers and logs destruction telemetry.
- `test_health_check_loop_cycles_and_logs`: drives the async loop through success, failure, recovery, and graceful cancellation, asserting emitted diagnostics.
- `test_create_sandbox_uses_code_interpreter_when_generic_unavailable`: verifies fallback creation when generic templates are unavailable, asserting diagnostics and payload.
- `test_scale_pool_trims_heterogeneous_templates`: ensures heterogeneous pools trim idle sandboxes without impacting busy code interpreter instances.

## Diagnostic Log Samples

```text
INFO  Created new E2B sandbox: stub-1
WARNING Sandbox creation failed (attempt 1/3): transient network error
INFO  Recovered E2B sandbox creation on attempt 3: flaky-1
ERROR Failed to create E2B sandbox: quota hard fail
ERROR Sandbox creation exhausted retries (2 attempts)
INFO  Destroyed E2B sandbox: sb-old
WARNING Sandbox sb-slow response degraded (6.50s)
ERROR Sandbox pool exhausted: 1 active of max 1
INFO  Destroyed E2B sandbox: sb-1
INFO  Destroyed E2B sandbox: sb-2
INFO  Created new E2B sandbox: ci-1
INFO  Destroyed E2B sandbox: audio-1
INFO  Destroyed E2B sandbox: ml-1
ERROR Health check error: synthetic health failure
```

All entries originate from `src.core.e2b.sandbox_manager` and are captured via `caplog`, ensuring future regressions surface as log mismatches.

## Blind Spots and Future Coverage

1. Health loop coverage now includes cancellation and recovery, but long-running drift detection (hours-long windows) still needs synthetic timers.
2. Scale-in trimming validated for mixed pools; quota-aware downsizing across heterogeneous workloads remains TODO.
3. Code Interpreter fallbacks now covered via stubs; integrate real SDK toggles when upstream support lands.
4. Long-lived sandboxes and file transfer helpers are not exercised; consider integration hooks once fixture assets are available.

## Corner Cases & Observations

- Scale-in trimming confirmed that only idle healthy sandboxes are destroyed; busy instances remain untouched, protecting in-flight work across template types.
- The async health loop continues after synthetic failures, emitting a single error per fault and resuming normal operation, which matches the desired resilience profile.
- No surprise system interactions surfaced beyond the expected logging cadence; cancellation occurs cleanly once the scheduler raises `CancelledError`.
- Code interpreter fallback validated that template unavailability still provisions running sandboxes without leaking credentials or bypassing logging.
- Quota-pressure trimming reclaimed the oldest idle sandboxes first, ensuring newer or busy workloads and degraded diagnostics remain available for remediation.

## Impact on Pipeline Robustness

- The recovery, quota, and pool exhaustion paths align with the Datadog retry telemetry, ensuring consistent alerts across the monitoring stack.
- Verified lifecycle teardown prevents leaked sandboxes, preserving resource budgets for the ML inference pipeline and Tenebris cleanup flow.
- Degradation logging feeds into the pipeline health dashboard, enabling proactive remediation when throughput drops or latency spikes.
- The expanded tests provide regression safety before enabling automatic scaling in CI and production rollouts, and demonstrate that the health loop self-heals after intermittent faults.
