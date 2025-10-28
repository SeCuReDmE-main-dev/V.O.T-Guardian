"""Unit tests for PostgreSQLClient helpers."""

import asyncio
import json
from typing import Any
from unittest import mock

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
        async def acquire(self):
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
