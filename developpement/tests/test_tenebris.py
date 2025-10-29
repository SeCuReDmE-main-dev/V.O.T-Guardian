"""Tests for the Tenebris security protocol."""

import json
import logging
import types

import pytest

from src.core.security import tenebris as tenebris_module
from src.core.security.tenebris import (
    TenebrisConfig,
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
@pytest.mark.parametrize("encryption_enabled", [True, False])
async def test_cleanup_clears_sandbox_and_keys(encryption_enabled):
    config = TenebrisConfig(encryption_enabled=encryption_enabled)
    protocol = TenebrisProtocol(config=config)

    async with protocol.execute_protocol("call-cleanup") as sandbox_id:
        session_id, session_state = next(
            iter(protocol._active_sessions.items())
        )
        assert session_state.get("sandbox_id") == sandbox_id
        if encryption_enabled:
            assert session_state.get("encryption_key") is not None
        else:
            assert session_state.get("encryption_key") is None

    assert protocol._active_sessions == {}

    purge_events = [
        json.loads(event["text"])
        for event in _DatadogRecorder.events
        if event.get("title") == "Tenebris Protocol: TENEBRIS_PURGE_COMPLETE"
    ]
    assert purge_events
    purge_metadata = purge_events[0].get("metadata", {})
    assert "sandbox_id" not in purge_metadata
    assert "encryption_key" not in purge_metadata

    serialized_state = json.dumps(protocol._active_sessions)
    assert "sb_" not in serialized_state

    report = protocol.get_compliance_report()
    assert report["active_sessions"] == 0
    assert report["completed_sessions"] == 0
    assert report["compliance_rate"] == 100


@pytest.mark.anyio
async def test_destroyed_sandbox_access_logs_violation(monkeypatch, caplog):
    caplog.set_level(logging.WARNING, logger=LOGGER)

    protocol = TenebrisProtocol()

    async def already_destroyed(session_id: str):
        protocol.logger.warning("Sandbox already destroyed for %s", session_id)
        raise RuntimeError("sandbox already destroyed")

    monkeypatch.setattr(protocol, "_destroy_e2b_sandbox", already_destroyed)

    with pytest.raises(TenebrisViolationException):
        async with protocol.execute_protocol("call-stale"):
            pass

    payloads = _extract_event_payloads()
    assert any(
        p.get("event_type") == "TENEBRIS_DESTRUCTION_FAILED"
        for p in payloads
    )
    assert not any(
        p.get("event_type") == "TENEBRIS_PURGE_COMPLETE"
        for p in payloads
    )

    assert any(
        "Sandbox already destroyed" in record.message
        for record in caplog.records
    )

    status = protocol.get_protocol_status("call-stale")
    assert status.get("status") == "violation"

    session_id = status.get("session_id")
    assert session_id is not None
    assert "error" in protocol._active_sessions[session_id]


@pytest.mark.anyio
async def test_key_revocation_violation_records_diagnostics(
    monkeypatch,
    caplog,
):
    caplog.set_level(logging.ERROR, logger=LOGGER)

    protocol = TenebrisProtocol()

    async def failing_revoke(session_id: str):
        protocol.logger.error(
            "Unauthorized key access while revoking for %s",
            session_id,
        )
        raise PermissionError("unauthorized key access")

    monkeypatch.setattr(protocol, "_revoke_crypto_keys", failing_revoke)

    with pytest.raises(TenebrisViolationException):
        async with protocol.execute_protocol("call-unauthorized"):
            pass

    payloads = _extract_event_payloads()
    failure_events = [
        p for p in payloads
        if p.get("event_type") == "TENEBRIS_DESTRUCTION_FAILED"
    ]
    assert failure_events
    metadata = failure_events[0].get("metadata", {})
    assert metadata.get("call_id") == "call-unauthorized"
    assert "unauthorized" in metadata.get("error", "")

    assert any(
        "Unauthorized key access" in record.message
        for record in caplog.records
    )

    status = protocol.get_protocol_status("call-unauthorized")
    assert status.get("status") == "violation"


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
