import json
from unittest.mock import patch

import pytest

from src.core.monitoring.local_telemetry import LocalTelemetry, local_endpoint
from src.config.settings import Settings


class Response:
    status = 200
    def __init__(self, body=b"{}"): self.body = body
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, limit): return self.body[:limit]


def test_no_telemetry_without_explicit_enablement():
    with patch.dict("os.environ", {"DD_API_KEY": "unused-secret"}, clear=True), patch("urllib.request.build_opener") as transport:
        assert not LocalTelemetry().record_metric("vot.analysis.total", 1)
        transport.assert_not_called()


@pytest.mark.parametrize("endpoint", ["https://example.invalid/v1/metrics", "http://localhost:4318/v1/metrics", "http://127.0.0.1:4318/v1/metrics?token=x", "http://user:password@127.0.0.1:4318/v1/metrics", "http://127.0.0.1:8125/v1/metrics"])
def test_remote_or_credentialled_endpoints_are_rejected(endpoint):
    assert not local_endpoint(endpoint)


def test_only_technical_metrics_cross_the_transport_without_identifiers():
    with patch.dict("os.environ", {"SECUREDME_OTEL_ENABLED": "true"}), patch("urllib.request.build_opener") as factory:
        factory.return_value.open.return_value = Response()
        client = LocalTelemetry()
        assert client.record_metric("vot.analysis.latency_ms", 10.2, {"call_id": "private-call", "reference": "private-hash"})
        sent = factory.return_value.open.call_args.args[0].data
        payload = json.loads(sent)
        metric = payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"][0]
        assert metric["gauge"]["dataPoints"][0]["asDouble"] == 10.2
        assert "private" not in sent.decode()
        factory.return_value.open.reset_mock()
        assert not client.record_metric("vot.analysis.confidence", .93)
        assert not client.record_metric("vot.audio.snr_db", 20)
        assert not client.record_metric("vot.analysis.prediction.ai", 1)
        factory.return_value.open.assert_not_called()


@pytest.mark.parametrize("value", [float("inf"), float("nan"), -1, True, "1", .5])
def test_invalid_counter_values_are_rejected(value):
    with patch.dict("os.environ", {"SECUREDME_OTEL_ENABLED": "true"}), patch("urllib.request.build_opener") as transport:
        assert not LocalTelemetry().record_metric("vot.analysis.total", value)
        transport.assert_not_called()


@pytest.mark.parametrize("response", [b"[]", b"not-json", b"x" * 8193, b'{"partialSuccess":{"rejectedDataPoints":"1"}}'])
def test_collector_failure_does_not_report_success(response):
    with patch.dict("os.environ", {"SECUREDME_OTEL_ENABLED": "true"}), patch("urllib.request.build_opener") as factory:
        factory.return_value.open.return_value = Response(response)
        assert not LocalTelemetry().record_metric("vot.analysis.total", 1)


def test_outage_is_fail_open_and_authentication_readiness_is_independent():
    with patch.dict("os.environ", {"SECUREDME_OTEL_ENABLED": "true"}), patch("urllib.request.build_opener") as factory:
        factory.return_value.open.side_effect = OSError("private-error")
        assert not LocalTelemetry().record_metric("vot.analysis.total", 1)
    settings = Settings(api_secret_key="test-key", e2b_api_key="test-key", log_level="ERROR", encryption_enabled=True)
    assert settings.is_production_ready()
    settings.api_secret_key = ""
    assert not settings.is_production_ready()
