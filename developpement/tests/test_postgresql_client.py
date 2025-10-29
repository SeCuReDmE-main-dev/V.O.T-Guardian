"""Unit tests for PostgreSQLClient helpers."""

import asyncio
import json
from typing import Any
from unittest import mock

import pytest

from src.core.database.postgresql_client import PostgreSQLClient


class DummyRecord(dict):
    """Minimal stand-in for asyncpg.Record that behaves like a dict."""

    def __getattr__(self, item: str) -> Any:  # pragma: no cover - safety net
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc


def test_get_analysis_result_deserializes_features():
    client = PostgreSQLClient()

    fake_row = DummyRecord(
        id=1,
        call_id="call_test_123",
        prediction="AI",
        confidence=0.87,
        features=json.dumps({
            "vot": 0.4,
            "jitter": 0.01,
            "snr_db": 18.5,
            "shimmer": 0.12,
            "mfcc_mean": -123.4,
            "thd_percent": 0.8,
            "spectral_centroid": 456.7,
            "zero_crossing_rate": 0.05,
        }),
        processing_time_ms=123.4,
        created_at=mock.Mock(isoformat=lambda: "2025-10-28T12:34:56"),
    )

    async def fake_fetchrow(query: str, call_id: str):
        assert "analysis_results" in query
        assert call_id == "call_test_123"
        return fake_row

    class DummyPool:
        def acquire(self):
            return self

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def fetchrow(self, *args, **kwargs):
            return await fake_fetchrow(*args, **kwargs)

    client.pool = DummyPool()

    result = asyncio.run(client.get_analysis_result("call_test_123"))

    assert isinstance(result, dict)
    assert result["call_id"] == "call_test_123"
    features = result["features"]
    assert isinstance(features, dict)
    for field in (
        "vot",
        "jitter",
        "snr_db",
        "shimmer",
        "mfcc_mean",
        "thd_percent",
        "spectral_centroid",
        "zero_crossing_rate",
    ):
        assert field in features


class _DummyAcquire:
    """Async context manager returning a stub connection."""

    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover - passthrough
        return False


class _DummyPool:
    """Pool returning the provided connection."""

    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _DummyAcquire(self._conn)


def test_store_analysis_result_logs_and_raises_on_error(caplog):
    client = PostgreSQLClient()
    caplog.set_level("ERROR", logger="src.core.database.postgresql_client")

    class FailingConnection:
        async def execute(self, *args, **kwargs):  # pragma: no cover - exercised via test
            raise RuntimeError("constraint violation")

    client.pool = _DummyPool(FailingConnection())

    async def run_store():
        await client.store_analysis_result({
            "call_id": "dup-call",
            "prediction": "AI",
            "confidence": 0.91,
            "features": {"mfcc": [0.1, 0.2]},
            "processing_time_ms": 87.5,
        })

    with pytest.raises(RuntimeError):
        asyncio.run(run_store())

    assert any(
        "Error storing analysis result" in record.message
        and "constraint violation" in record.message
        for record in caplog.records
    )


def test_get_analysis_result_invalid_json_logs_and_returns_raw(caplog):
    client = PostgreSQLClient()
    caplog.set_level("DEBUG", logger="src.core.database.postgresql_client")

    fake_row = DummyRecord(
        id=42,
        call_id="call_bad_json",
        prediction="AI",
        confidence=0.77,
        features="{invalid json}",
        processing_time_ms=55.5,
        created_at=mock.Mock(isoformat=lambda: "2025-10-29T08:15:00"),
    )

    class FakeConnection:
        async def fetchrow(self, query: str, call_id: str):
            assert call_id == "call_bad_json"
            return fake_row

    client.pool = _DummyPool(FakeConnection())

    result = asyncio.run(client.get_analysis_result("call_bad_json"))

    assert result is not None
    assert result["features"] == "{invalid json}"
    assert any(
        "Failed to decode features JSON" in record.message
        for record in caplog.records
    )


def test_get_compliance_report_handles_zero_activity():
    client = PostgreSQLClient()

    class ReportingConnection:
        async def fetchrow(self, query: str, *_args):
            if "analysis_results" in query:
                return DummyRecord(
                    total_analyses=0,
                    ai_predictions=0,
                    human_predictions=0,
                    avg_confidence=None,
                    avg_processing_time=None,
                )
            assert "audit_trail" in query
            return DummyRecord(
                total_events=0,
                compliant_events=0,
                degraded_events=0,
            )

    client.pool = _DummyPool(ReportingConnection())

    report = asyncio.run(
        client.get_compliance_report("2025-01-01", "2025-01-31")
    )

    assert "error" not in report
    assert report["analysis"]["total"] == 0
    assert report["analysis"]["average_confidence"] == 0.0
    assert report["audit"]["compliance_rate"] == 100
    assert report["period"] == {
        "start": "2025-01-01",
        "end": "2025-01-31",
    }
