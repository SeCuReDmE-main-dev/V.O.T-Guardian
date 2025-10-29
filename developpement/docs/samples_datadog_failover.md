# Datadog Failover Log Samples

The following excerpts were generated while running the new failover-oriented tests in `tests/test_datadog_client.py` on 2025-10-28.

## 1. Missing API key at startup

```
ERROR src.core.monitoring.datadog_client Datadog failover - Datadog SDK unavailable; monitoring operating in degraded mode
ERROR src.core.monitoring.datadog_client Datadog failover - API key missing; Datadog integrations disabled
```

- Scenario: `DatadogClient` instantiated with an empty API key. 
- Outcome: Client switches to failover mode, leaving event and metric transports disabled while surfacing the diagnostic in logs.

## 2. StatsD timeout during metric recording

```
ERROR src.core.monitoring.datadog_client Datadog failover - Failed to record metric: statsd timeout
```

- Scenario: `_FailingStatsd` stub raises `TimeoutError` during histogram submission.
- Outcome: Client emits failover log but keeps the pipeline running, allowing the caller to continue execution.

## 3. Event publishing failure with retries

```
ERROR src.core.monitoring.datadog_client Datadog failover - Failed to log event to Datadog: datadog timeout
ERROR src.core.monitoring.datadog_client Datadog failover - Failed to log event to Datadog: datadog timeout
```

- Scenario: `EventsApi.create_event` stub throws on every call to emulate a network outage.
- Outcome: Each attempt triggers a failover diagnostic, demonstrating visibility for consecutive retries.

## 4. Cascaded monitoring degradation

```
WARNING src.core.monitoring.datadog_client Datadog failover - Events API unavailable; event buffered locally
WARNING src.core.monitoring.datadog_client Datadog failover - StatsD client unavailable; metric dropped
```

- Scenario: Datadog SDK unavailable; client attempts to send both events and metrics.
- Outcome: Logs document the chained fallback (events buffered, metrics dropped) while allowing the rest of the analysis pipeline to complete without raising exceptions.

## Remaining scenarios to capture

- Successful metric and event dispatch traces for observability baselines.
- Retry backoff metadata once asynchronous transport retries are implemented.
```}