"""Tests for the Tenebris security protocol."""

import json
import logging
import types

import pytest

from src.core.security import tenebris as tenebris_module
from src.core.security.tenebris import (
    TenebrisProtocol,
    TenebrisViolationException,
)

LOGGER = "src.core.security.tenebris"


class _DatadogRecorder:
    events = []

    class Event:
        @staticmethod
        def create(**payload):
            _DatadogRecorder.events.append(payload)


@pytest.fixture(autouse=True)
def reset_datadog_stub(monkeypatch):
    _DatadogRecorder.events = []
    monkeypatch.setattr(
        tenebris_module,
        "datadog_api",
        _DatadogRecorder,
        raising=False,
    )
    yield


@pytest.fixture
def anyio_backend():
    """Force async tests to run on asyncio backend."""
    return "asyncio"


def _event_types() -> list[str]:
    return [payload.get("title", "") for payload in _DatadogRecorder.events]


def _extract_event_payloads() -> list[dict[str, object]]:
    payloads = []
    for event in _DatadogRecorder.events:
        text = event.get("text", "{}")
        try:
            payloads.append(json.loads(text))
        except json.JSONDecodeError:
            payloads.append({})
    return payloads


@pytest.mark.anyio
async def test_execute_protocol_success_logs_and_cleans(caplog):
    caplog.set_level(logging.INFO, logger=LOGGER)

    protocol = TenebrisProtocol()

    async with protocol.execute_protocol("call-success") as sandbox_id:
        assert sandbox_id.startswith("sb_call-success_")

    titles = _event_types()
    assert "Tenebris Protocol: TENEBRIS_START" in titles
    assert "Tenebris Protocol: TENEBRIS_PURGE_COMPLETE" in titles

    payloads = _extract_event_payloads()
    assert any(
        p.get("event_type") == "TENEBRIS_PURGE_COMPLETE"
        for p in payloads
    )
    assert protocol._active_sessions == {}
    assert any(
        "Destroying E2B sandbox" in record.message
        for record in caplog.records
    )


@pytest.mark.anyio
async def test_execute_protocol_violation_emits_audit(monkeypatch):
    protocol = TenebrisProtocol()

    async def failing_create(
        session_id: str,
        call_id: str,
        encryption_key: bytes,
    ):
        raise RuntimeError("sandbox failure")

    monkeypatch.setattr(protocol, "_create_isolated_sandbox", failing_create)

    with pytest.raises(TenebrisViolationException):
        async with protocol.execute_protocol("call-failure"):
            pass

    payloads = _extract_event_payloads()
    assert any(p.get("event_type") == "TENEBRIS_VIOLATION" for p in payloads)


@pytest.mark.anyio
async def test_audit_event_failure_logs_error(monkeypatch, caplog):
    caplog.set_level(logging.ERROR, logger=LOGGER)

    class RaisingEvent:
        @staticmethod
        def create(**payload):
            raise RuntimeError("datadog down")

    monkeypatch.setattr(
        tenebris_module,
        "datadog_api",
        types.SimpleNamespace(Event=RaisingEvent),
        raising=False,
    )

    protocol = TenebrisProtocol()
    await protocol._log_audit_event("TEST", {"foo": "bar"})

    assert any(
        "Failed to log audit event" in record.message
        for record in caplog.records
    )
