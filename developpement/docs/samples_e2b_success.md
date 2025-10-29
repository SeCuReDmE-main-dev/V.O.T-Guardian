# E2B Sandbox Success & Degradation Samples

Sourced from `tests/test_e2b_sandbox_manager.py` (2025-10-28).

## Lifecycle startup

```text
INFO src.core.e2b.sandbox_manager Created new E2B sandbox: stub-1
INFO src.core.e2b.sandbox_manager Destroyed E2B sandbox: stub-1
```

- Confirmed during `test_sandbox_lifecycle_happy_path` while cycling a sandbox through acquisition and teardown.

## Health degradation

```text
WARNING src.core.e2b.sandbox_manager Sandbox sb-slow response degraded (6.50s)
```

- Emitted when the health-check loop observed a simulated slow response, marking the sandbox as `degraded`.

## Pool exhaustion

```text
ERROR src.core.e2b.sandbox_manager Sandbox pool exhausted: 1 active of max 1
```

- Triggered when `_acquire_sandbox` detected all instances at capacity, ensuring the system surfaces the critical condition instead of silently blocking.

## Upcoming success scenarios

- Document recovery logs when degraded sandboxes return to healthy state.
- Capture scale-in events once idle-sandbox reclamation paths are covered by tests.
