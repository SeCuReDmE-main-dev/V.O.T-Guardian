# Tenebris Protocol Success Samples

Extracted from `tests/test_tenebris.py::test_execute_protocol_success_logs_and_cleans` (2025-10-28).

## Audit events

```text
Tenebris Protocol: TENEBRIS_START
Tenebris Protocol: TENEBRIS_PURGE_COMPLETE
```

- The first entry confirms protocol activation with sandbox and session identifiers.
- The purge completion record verifies the auto-destruction SLA and compliance metadata.

## Logger trace

```text
INFO src.core.security.tenebris Destroying E2B sandbox for session tenebris_call-success_...
```

- Destruction step executes at the end of the context manager.
- Confirms the pipeline proceeds without raising, while emitting operational observability.

## Follow-up success cases

- Capture key rotation logs when rotating Tenebris encryption material mid-session.
- Record manual override flows (e.g., forced purge) once implemented to document non-automatic cleanups.
