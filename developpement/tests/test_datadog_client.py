"""Failover tests for the Datadog monitoring client."""

import logging
from typing import List

import pytest

from src.core.monitoring import datadog_client as datadog_module
from src.core.monitoring.datadog_client import DatadogClient, DatadogConfig


class _FailingStatsd:
    """StatsD stub that raises to emulate network outages."""

    def __init__(self):
        self.calls: List[str] = []

    def histogram(self, name, value, *, tags=None):  # pragma: no cover - exercised via tests
        self.calls.append("histogram")
        raise TimeoutError("statsd timeout")

    def increment(self, name, value, *, tags=None):  # pragma: no cover - exercised via tests
        self.calls.append("increment")
        raise TimeoutError("statsd timeout")

    def gauge(self, name, value, *, tags=None):  # pragma: no cover - exercised via tests
        self.calls.append("gauge")
        raise TimeoutError("statsd timeout")


@pytest.fixture(autouse=True)
def reset_datadog_module(monkeypatch):
    """Ensure each test starts from a clean availability flag."""
    monkeypatch.setattr(datadog_module, "DATADOG_AVAILABLE", False, raising=False)
    yield


def test_missing_api_key_triggers_failover_logs(monkeypatch, caplog):
    caplog.set_level(logging.WARNING, logger="src.core.monitoring.datadog_client")

    client = DatadogClient(config=DatadogConfig(api_key=""))

    assert client.events_api is None
    failover_messages = [
        record.message
        for record in caplog.records
        if "Datadog failover" in record.message
    ]
    assert any("API key missing" in msg for msg in failover_messages)
    assert any("SDK unavailable" in msg for msg in failover_messages)


def test_record_metric_failure_logs_failover_without_raising(monkeypatch, caplog):
    caplog.set_level(logging.ERROR, logger="src.core.monitoring.datadog_client")

    def fake_init_statsd(self):
        self.statsd = _FailingStatsd()

    monkeypatch.setattr(DatadogClient, "_initialize_statsd", fake_init_statsd)

    client = DatadogClient(config=DatadogConfig(api_key="token"))

    client.record_metric("vot.analysis.latency_ms", 125.0)

    failover_messages = [
        record.message
        for record in caplog.records
        if "Datadog failover" in record.message
    ]
    assert any("metric send failed" in msg for msg in failover_messages)
    assert client._failover_active is True


@pytest.mark.anyio
async def test_log_event_network_failure_records_failover(monkeypatch, caplog):
    caplog.set_level(logging.ERROR, logger="src.core.monitoring.datadog_client")

    class StubConfiguration:
        def __init__(self):
            self.api_key = {'apiKeyAuth': None, 'appKeyAuth': None}
            self.server_variables = {'site': None}

    class StubApiClient:
        def __init__(self, configuration):
            self.configuration = configuration

    class FailingEventsApi:
        def __init__(self, api_client):
            self.api_client = api_client
            self.calls = 0

        def create_event(self, request):  # pragma: no cover - exercised via test
            self.calls += 1
            raise TimeoutError("datadog timeout")

    monkeypatch.setattr(datadog_module, "DATADOG_AVAILABLE", True, raising=False)
    monkeypatch.setattr(datadog_module, "Configuration", StubConfiguration, raising=False)
    monkeypatch.setattr(datadog_module, "ApiClient", StubApiClient, raising=False)
    monkeypatch.setattr(datadog_module, "EventsApi", FailingEventsApi, raising=False)

    async def fake_init_statsd(self):
        self.statsd = None

    monkeypatch.setattr(DatadogClient, "_initialize_statsd", fake_init_statsd)

    client = DatadogClient(config=DatadogConfig(api_key="token", app_key="app"))

    await client.log_event("Test", {"key": "value"})
    await client.log_event("Test", {"key": "value"})

    failover_messages = [
        record.message
        for record in caplog.records
        if "Datadog failover" in record.message
    ]
    matching = [
        message
        for message in failover_messages
        if "Failed to log event" in message
    ]
    assert len(matching) == 2


@pytest.mark.anyio
async def test_failover_chain_captures_all_diagnostics(caplog):
    caplog.set_level(logging.WARNING, logger="src.core.monitoring.datadog_client")

    client = DatadogClient(config=DatadogConfig(api_key="chain"))

    await client.log_event("Chain", {"stage": 1})
    client.record_analysis_metrics("call-123", "AI", 0.91, 742.0)

    failover_messages = [
        record.message
        for record in caplog.records
        if "Datadog failover" in record.message
    ]
    assert any("Events API unavailable" in msg for msg in failover_messages)
    assert any("StatsD client unavailable" in msg for msg in failover_messages)