# Datadog Success Telemetry Samples

Captured during `tests/test_datadog_client.py::test_metric_success_logs_without_failover` and `test_log_event_success_emits_info` (2025-10-28).

## Metric publication

```text
INFO src.core.monitoring.datadog_client Datadog metric recorded: vot.analysis.latency_ms
```

- Scenario: StatsD reachable; latency histogram submitted with regional tag.
- Outcome: Metric routed without triggering failover, `_failover_active` remains `False`.

## Event publication

```text
INFO src.core.monitoring.datadog_client Datadog event published: Deployment
```

- Scenario: Datadog Events API responds successfully.
- Outcome: EventCreateRequest hits the stub transport, confirming observability on success-path signals.

## Next success scenarios to capture

- Metrics batching across multiple calls to verify tag aggregation behaviour.
- Event publication with custom tags and secondary alert types.
