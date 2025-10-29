"""Failover tests for the Datadog monitoring client."""

import logging
from typing import List, Optional


import pytest

from src.core.monitoring import datadog_client as datadog_module
from src.core.monitoring.datadog_client import DatadogClient, DatadogConfig


LOGGER = "src.core.monitoring.datadog_client"


class _StubConfiguration:
    def __init__(self):
        self.api_key = {'apiKeyAuth': None, 'appKeyAuth': None}
        self.server_variables = {'site': None}


class _StubApiClient:
    def __init__(self, configuration):
        self.configuration = configuration


class _RecorderEventsApi:
    instances: List["_RecorderEventsApi"] = []

    def __init__(self, api_client):
        self.api_client = api_client
        self.requests = []
        _RecorderEventsApi.instances.append(self)

    def create_event(self, request):
        self.requests.append(request)


class _ConfigurableEventsApi:
    """Events API stub that fails a preset number of attempts."""

    failures: int = 0

    def __init__(self, api_client):
        self.api_client = api_client
        self.calls = 0
        self.requests = []

    def create_event(self, request):
        self.calls += 1
        self.requests.append(request)
        if _ConfigurableEventsApi.failures > 0:
            _ConfigurableEventsApi.failures -= 1
            raise TimeoutError("datadog timeout")


class _RecorderStatsd:
    def __init__(self):
        self.calls: List[tuple[str, str, float, Optional[List[str]]]] = []

    def histogram(self, name, value, *, tags=None):
        self.calls.append(("histogram", name, value, tags))

    def increment(self, name, value, *, tags=None):
        self.calls.append(("increment", name, value, tags))

    def gauge(self, name, value, *, tags=None):
        self.calls.append(("gauge", name, value, tags))


class _FailingStatsd:
    """StatsD stub that raises to emulate network outages."""

    def __init__(self):
        self.calls: List[str] = []

    def histogram(self, name, value, *, tags=None):
        """Always raise to mimic histogram failure."""
        self.calls.append("histogram")
        raise TimeoutError("statsd timeout")

    def increment(self, name, value, *, tags=None):
        """Always raise to mimic counter failure."""
        self.calls.append("increment")
        raise TimeoutError("statsd timeout")

    def gauge(self, name, value, *, tags=None):
        """Always raise to mimic gauge failure."""
        self.calls.append("gauge")
        raise TimeoutError("statsd timeout")


class _FlakyStatsd:
    """StatsD stub that fails a configurable number of attempts."""

    def __init__(self, failures: int):
        self.remaining = failures
        self.calls: List[str] = []

    def _maybe_fail(self, method: str):
        self.calls.append(method)
        if self.remaining > 0:
            self.remaining -= 1
            raise TimeoutError("transient statsd failure")

    def histogram(self, name, value, *, tags=None):
        self._maybe_fail("histogram")

    def increment(self, name, value, *, tags=None):
        self._maybe_fail("increment")

    def gauge(self, name, value, *, tags=None):
        self._maybe_fail("gauge")


@pytest.fixture(autouse=True)
def reset_datadog_module(monkeypatch):
    """Ensure each test starts from a clean availability flag."""
    monkeypatch.setattr(
        datadog_module,
        "DATADOG_AVAILABLE",
        False,
        raising=False,
    )
    _ConfigurableEventsApi.failures = 0
    yield


@pytest.fixture
def anyio_backend():
    """Force anyio-based tests to run with asyncio backend."""
    return "asyncio"


def _enable_datadog(
    monkeypatch,
    *,
    statsd: Optional[_RecorderStatsd] = None,
    events_cls=None,
):
    """Configure Datadog module with stubbed SDK objects for success paths."""
    monkeypatch.setattr(
        datadog_module,
        "DATADOG_AVAILABLE",
        True,
        raising=False,
    )
    monkeypatch.setattr(
        datadog_module,
        "Configuration",
        _StubConfiguration,
        raising=False,
    )
    monkeypatch.setattr(
        datadog_module,
        "ApiClient",
        _StubApiClient,
        raising=False,
    )
    monkeypatch.setattr(
        datadog_module,
        "EventsApi",
        events_cls or _RecorderEventsApi,
        raising=False,
    )

    if statsd is not None:
        def fake_init_statsd(self):
            self.statsd = statsd

        monkeypatch.setattr(
            DatadogClient,
            "_initialize_statsd",
            fake_init_statsd,
        )


def test_metric_success_logs_without_failover(monkeypatch, caplog):
    statsd = _RecorderStatsd()
    _enable_datadog(monkeypatch, statsd=statsd)

    caplog.set_level(logging.INFO, logger=LOGGER)

    client = DatadogClient(
        config=DatadogConfig(api_key="token", app_key="app")
    )

    client.record_metric("vot.analysis.latency_ms", 128.0, {"region": "ca"})

    assert statsd.calls, "StatsD call not recorded"
    method, metric, value, tags = statsd.calls[0]
    assert method == "histogram"
    assert metric == "vot.analysis.latency_ms"
    assert value == 128.0
    assert tags is not None
    assert any(tag.startswith("region:") for tag in tags)

    success_logs = [
        record.message for record in caplog.records
        if "Datadog metric recorded" in record.message
    ]
    assert success_logs
    assert client._failover_active is False


def test_metric_retry_chain_recovers(monkeypatch, caplog):
    flaky = _FlakyStatsd(failures=2)
    _enable_datadog(monkeypatch, statsd=flaky)

    caplog.set_level(logging.INFO, logger=LOGGER)

    client = DatadogClient(
        config=DatadogConfig(
            api_key="token",
            app_key="app",
            max_retries=3,
            retry_backoff_seconds=0,
        )
    )

    client.record_metric("vot.analysis.latency_ms", 64.0)

    assert flaky.calls.count("histogram") == 3
    assert any(
        "Datadog retry scheduled for metric" in record.message
        for record in caplog.records
    )
    assert any(
        "Datadog metric recorded" in record.message
        for record in caplog.records
    )
    assert client._failover_active is False


def test_metric_retry_chain_exhausts(monkeypatch, caplog):
    failing = _FailingStatsd()
    _enable_datadog(monkeypatch, statsd=failing)

    caplog.set_level(logging.ERROR, logger=LOGGER)

    client = DatadogClient(
        config=DatadogConfig(
            api_key="token",
            max_retries=2,
            retry_backoff_seconds=0,
        )
    )

    client.record_metric("vot.analysis.latency_ms", 96.0)

    assert failing.calls == ["histogram", "histogram"]
    assert any(
        "Datadog metric permanently failed" in record.message
        for record in caplog.records
    )
    assert client._failover_active is True


@pytest.mark.anyio
async def test_log_event_success_emits_info(monkeypatch, caplog):
    statsd = _RecorderStatsd()
    _enable_datadog(monkeypatch, statsd=statsd)

    _RecorderEventsApi.instances.clear()

    caplog.set_level(logging.INFO, logger=LOGGER)

    client = DatadogClient(
        config=DatadogConfig(api_key="token", app_key="app")
    )

    await client.log_event(
        "Deployment",
        {"status": "ok"},
        alert_type="success",
    )

    assert _RecorderEventsApi.instances, "Events API stub not instantiated"
    requests = _RecorderEventsApi.instances[0].requests
    assert len(requests) == 1
    assert getattr(requests[0], "title", "") == "Deployment"

    info_logs = [
        record.message for record in caplog.records
        if "Datadog event published" in record.message
    ]
    assert info_logs
    assert client._failover_active is False


@pytest.mark.anyio
async def test_log_event_retry_chain_recovers(monkeypatch, caplog):
    statsd = _RecorderStatsd()
    _ConfigurableEventsApi.failures = 2
    _enable_datadog(
        monkeypatch,
        statsd=statsd,
        events_cls=_ConfigurableEventsApi,
    )

    caplog.set_level(logging.INFO, logger=LOGGER)

    client = DatadogClient(
        config=DatadogConfig(
            api_key="token",
            app_key="app",
            max_retries=3,
            retry_backoff_seconds=0,
        )
    )

    await client.log_event("RetryEvent", {"stage": "retry"})

    assert client.events_api.calls == 3
    assert any(
        "Datadog retry scheduled for event" in record.message
        for record in caplog.records
    )
    assert any(
        "Datadog event published" in record.message
        for record in caplog.records
    )
    assert client._failover_active is False


@pytest.mark.anyio
async def test_log_event_retry_chain_exhausts(monkeypatch, caplog):
    statsd = _RecorderStatsd()
    _ConfigurableEventsApi.failures = 5
    _enable_datadog(
        monkeypatch,
        statsd=statsd,
        events_cls=_ConfigurableEventsApi,
    )

    caplog.set_level(logging.ERROR, logger=LOGGER)

    client = DatadogClient(
        config=DatadogConfig(
            api_key="token",
            app_key="app",
            max_retries=3,
            retry_backoff_seconds=0,
        )
    )

    await client.log_event("RetryEvent", {"stage": "fail"})

    assert client.events_api.calls == 3
    assert any(
        "Datadog event permanently failed" in record.message
        for record in caplog.records
    )
    assert client._failover_active is True


def test_missing_api_key_triggers_failover_logs(monkeypatch, caplog):
    caplog.set_level(logging.WARNING, logger=LOGGER)

    client = DatadogClient(config=DatadogConfig(api_key=""))

    assert client.events_api is None
    failover_messages = [
        record.message
        for record in caplog.records
        if "Datadog failover" in record.message
    ]
    assert any("API key missing" in msg for msg in failover_messages)
    assert any("SDK unavailable" in msg for msg in failover_messages)


def test_metric_failover_logs_without_raising(monkeypatch, caplog):
    caplog.set_level(logging.ERROR, logger=LOGGER)

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
    assert any("Failed to record metric" in msg for msg in failover_messages)
    assert client._failover_active is True


@pytest.mark.anyio
async def test_log_event_network_failure_records_failover(monkeypatch, caplog):
    caplog.set_level(logging.ERROR, logger=LOGGER)

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

        def create_event(self, request):
            self.calls += 1
            raise TimeoutError("datadog timeout")

    monkeypatch.setattr(
        datadog_module,
        "DATADOG_AVAILABLE",
        True,
        raising=False,
    )
    monkeypatch.setattr(
        datadog_module,
        "Configuration",
        StubConfiguration,
        raising=False,
    )
    monkeypatch.setattr(
        datadog_module,
        "ApiClient",
        StubApiClient,
        raising=False,
    )
    monkeypatch.setattr(
        datadog_module,
        "EventsApi",
        FailingEventsApi,
        raising=False,
    )

    def fake_init_statsd(self):
        self.statsd = None

    monkeypatch.setattr(DatadogClient, "_initialize_statsd", fake_init_statsd)

    client = DatadogClient(
        config=DatadogConfig(api_key="token", app_key="app")
    )

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
    caplog.set_level(logging.WARNING, logger=LOGGER)

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
