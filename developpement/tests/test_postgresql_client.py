"""Unit tests for PostgreSQLClient helpers."""

import asyncio
import json
from typing import Any
from unittest import mock

import pytest

from src.core.database import postgresql_client as postgresql_module
from src.core.database.postgresql_client import PostgreSQLClient


@pytest.fixture
def anyio_backend():
    """Force anyio-driven tests to use the asyncio backend."""
    return "asyncio"


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

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ):  # pragma: no cover - passthrough
        return False


class _DummyPool:
    """Pool returning the provided connection."""

    def __init__(self, conn):
        self._conn = conn
        self.closed = False

    def acquire(self):
        return _DummyAcquire(self._conn)

    async def close(self):
        self.closed = True


class _DummyTransaction:
    """Asynchronous transaction stub tracking commit/rollback."""

    def __init__(self):
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.rolled_back = True
        else:
            self.committed = True
        return False


class _TransactionalConnection:
    """Base connection providing transaction context manager."""

    def __init__(self):
        self.transactions = []

    def transaction(self):
        tx = _DummyTransaction()
        self.transactions.append(tx)
        return tx

    async def execute(self, *_args, **_kwargs):
        return None


def test_store_analysis_result_logs_and_raises_on_error(caplog):
    client = PostgreSQLClient()
    caplog.set_level("ERROR", logger="src.core.database.postgresql_client")

    class FailingConnection(_TransactionalConnection):
        def __init__(self):
            super().__init__()

        async def execute(
            self,
            *args,
            **kwargs,
        ):  # pragma: no cover - exercised via test
            raise RuntimeError("constraint violation")

    failing_conn = FailingConnection()
    client.pool = _DummyPool(failing_conn)

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
    assert failing_conn.transactions
    assert failing_conn.transactions[0].rolled_back is True
    assert failing_conn.transactions[0].committed is False


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


def test_get_analysis_result_corrupted_numeric_logs_and_returns_none(caplog):
    client = PostgreSQLClient()
    caplog.set_level("ERROR", logger="src.core.database.postgresql_client")

    fake_row = DummyRecord(
        id=99,
        call_id="call_corrupted",
        prediction="AI",
        confidence="not-a-number",
        features=json.dumps({"vot": 0.41}),
        processing_time_ms="broken",
        created_at=mock.Mock(isoformat=lambda: "2025-10-29T09:45:00"),
    )

    class CorruptConnection:
        async def fetchrow(self, query: str, call_id: str):
            assert call_id == "call_corrupted"
            return fake_row

    client.pool = _DummyPool(CorruptConnection())

    result = asyncio.run(client.get_analysis_result("call_corrupted"))

    assert result is None
    assert any(
        "Error retrieving analysis result" in record.message
        and "could not convert string to float" in record.message
        for record in caplog.records
    )


def test_store_analysis_result_transaction_rolls_back_on_runtime_error(caplog):
    client = PostgreSQLClient()
    caplog.set_level("ERROR", logger="src.core.database.postgresql_client")

    class TxConnection(_TransactionalConnection):
        def __init__(self):
            super().__init__()
            self.executed_payloads = []

        async def execute(self, query, *params):
            self.executed_payloads.append((query, params))
            raise RuntimeError("synthetic failure during insert")

    tx_conn = TxConnection()
    client.pool = _DummyPool(tx_conn)

    async def do_store():
        await client.store_analysis_result({
            "call_id": "rollback-call",
            "prediction": "AI",
            "confidence": 0.66,
            "features": {"vot": 0.32},
            "processing_time_ms": 45.6,
        })

    with pytest.raises(RuntimeError, match="synthetic failure"):
        asyncio.run(do_store())

    assert tx_conn.transactions
    tx = tx_conn.transactions[0]
    assert tx.rolled_back is True
    assert tx.committed is False
    assert any(
        "Error storing analysis result" in record.message
        and "synthetic failure" in record.message
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


def test_get_compliance_report_handles_mixed_activity():
    client = PostgreSQLClient()

    class MixedConnection:
        async def fetchrow(self, query: str, *_args):
            if "analysis_results" in query:
                return DummyRecord(
                    total_analyses=8,
                    ai_predictions=5,
                    human_predictions=3,
                    avg_confidence=0.8125,
                    avg_processing_time=143.2,
                )
            return DummyRecord(
                total_events=6,
                compliant_events=4,
                degraded_events=2,
            )

    client.pool = _DummyPool(MixedConnection())

    report = asyncio.run(
        client.get_compliance_report("2025-02-01", "2025-02-28")
    )

    assert report["analysis"]["total"] == 8
    assert report["analysis"]["ai_predictions"] == 5
    assert report["analysis"]["average_confidence"] == pytest.approx(0.8125)
    assert report["analysis"]["average_processing_time_ms"] == pytest.approx(
        143.2
    )
    assert report["audit"]["compliance_rate"] == pytest.approx(
        66.666,
        rel=1e-3,
    )
    assert report["audit"]["degraded_events"] == 2


def test_get_compliance_report_logs_and_returns_error(caplog):
    client = PostgreSQLClient()
    caplog.set_level("ERROR", logger="src.core.database.postgresql_client")

    class FailingConnection:
        async def fetchrow(self, *args, **kwargs):
            raise RuntimeError("compliance query failed")

    client.pool = _DummyPool(FailingConnection())

    report = asyncio.run(
        client.get_compliance_report("2025-03-01", "2025-03-31")
    )

    assert report["error"] == "compliance query failed"
    assert any(
        "Error generating compliance report" in record.message
        for record in caplog.records
    )


@pytest.mark.anyio
async def test_connect_retries_then_succeeds(monkeypatch, caplog):
    caplog.set_level("INFO", logger="src.core.database.postgresql_client")

    attempt_outcomes = []
    fake_pool = _DummyPool(_TransactionalConnection())

    async def fake_create_pool(*_args, **_kwargs):
        if attempt_outcomes.count("fail") < 2:
            attempt_outcomes.append("fail")
            raise RuntimeError("connection refused")
        attempt_outcomes.append("success")
        return fake_pool

    delays = []

    async def fake_sleep(seconds):
        delays.append(seconds)

    monkeypatch.setattr(
        postgresql_module.asyncpg,
        "create_pool",
        fake_create_pool,
    )
    monkeypatch.setattr(postgresql_module.asyncio, "sleep", fake_sleep)

    client = PostgreSQLClient()
    client.config.connection_max_retries = 4
    client.config.connection_retry_backoff_seconds = 0.1

    await client.connect()

    assert attempt_outcomes == ["fail", "fail", "success"]
    assert delays == [0.1, 0.2]
    assert client.pool is fake_pool
    assert any(
        "Database connection attempt 1/4 failed" in record.message
        for record in caplog.records
    )
    assert any(
        "Connected to PostgreSQL database" in record.message
        for record in caplog.records
    )


@pytest.mark.anyio
async def test_connect_retries_exhaustion_raises(monkeypatch, caplog):
    caplog.set_level("ERROR", logger="src.core.database.postgresql_client")

    attempts = 0

    async def fake_create_pool(*_args, **_kwargs):
        nonlocal attempts
        attempts += 1
        raise RuntimeError("service unavailable")

    async def fake_sleep(_seconds):
        return None

    monkeypatch.setattr(
        postgresql_module.asyncpg,
        "create_pool",
        fake_create_pool,
    )
    monkeypatch.setattr(postgresql_module.asyncio, "sleep", fake_sleep)

    client = PostgreSQLClient()
    client.config.connection_max_retries = 2
    client.config.connection_retry_backoff_seconds = 0.05

    with pytest.raises(RuntimeError, match="service unavailable"):
        await client.connect()

    assert attempts == 2
    assert client.pool is None
    assert any(
        "Failed to connect to database after 2 attempts" in record.message
        for record in caplog.records
    )


class _InitFailurePool:
    """Pool stub capturing close calls for initialization failure tests."""

    def __init__(self):
        self.closed = False
        self.close_calls = 0

    async def close(self):
        self.close_calls += 1
        self.closed = True

    def acquire(self):
        return _DummyAcquire(_TransactionalConnection())


@pytest.mark.anyio
async def test_connect_initialization_failure_retries(monkeypatch, caplog):
    caplog.set_level("INFO", logger="src.core.database.postgresql_client")

    pools = []

    async def fake_create_pool(*_args, **_kwargs):
        pool = _InitFailurePool()
        pools.append(pool)
        return pool

    init_calls = 0

    async def fake_initialize(self):
        nonlocal init_calls
        init_calls += 1
        if init_calls == 1:
            raise RuntimeError("migration failure")

    delays = []

    async def fake_sleep(seconds):
        delays.append(seconds)

    monkeypatch.setattr(
        postgresql_module.asyncpg,
        "create_pool",
        fake_create_pool,
    )
    monkeypatch.setattr(
        PostgreSQLClient,
        "_initialize_tables",
        fake_initialize,
    )
    monkeypatch.setattr(postgresql_module.asyncio, "sleep", fake_sleep)

    client = PostgreSQLClient()
    client.config.connection_max_retries = 3
    client.config.connection_retry_backoff_seconds = 0.2

    await client.connect()

    assert len(pools) == 2
    assert pools[0].closed is True
    assert pools[1].closed is False
    assert client.pool is pools[1]
    assert delays == [0.2]
    assert any(
        "Database connection attempt 1/3 failed" in record.message
        for record in caplog.records
    )
    assert any(
        "Connected to PostgreSQL database" in record.message
        for record in caplog.records
    )


@pytest.mark.anyio
async def test_connect_initialization_failure_exhausts(monkeypatch, caplog):
    caplog.set_level("ERROR", logger="src.core.database.postgresql_client")

    pools = []

    async def fake_create_pool(*_args, **_kwargs):
        pool = _InitFailurePool()
        pools.append(pool)
        return pool

    async def fake_initialize(self):
        raise RuntimeError("schema init failed")

    async def fake_sleep(_seconds):
        return None

    monkeypatch.setattr(
        postgresql_module.asyncpg,
        "create_pool",
        fake_create_pool,
    )
    monkeypatch.setattr(
        PostgreSQLClient,
        "_initialize_tables",
        fake_initialize,
    )
    monkeypatch.setattr(postgresql_module.asyncio, "sleep", fake_sleep)

    client = PostgreSQLClient()
    client.config.connection_max_retries = 2

    with pytest.raises(RuntimeError, match="schema init failed"):
        await client.connect()

    assert len(pools) == 2
    assert all(pool.closed for pool in pools)
    assert client.pool is None
    assert any(
        "Failed to connect to database after 2 attempts" in record.message
        for record in caplog.records
    )


@pytest.mark.anyio
async def test_close_pool_with_metrics_emits_observability_logs(
    monkeypatch,
    caplog,
):
    caplog.set_level("INFO", logger="src.core.database.postgresql_client")
    client = PostgreSQLClient()

    class InstrumentedPool:
        def __init__(self):
            self.closed = False
            self.connection_count = 4

        async def close(self):
            await asyncio.sleep(0)
            self.closed = True

    pool = InstrumentedPool()

    memory_snapshots = iter([(4096, 0), (1024, 0)])
    perf_values = iter([10.0, 10.125])

    monkeypatch.setattr(
        postgresql_module.tracemalloc,
        "is_tracing",
        lambda: True,
    )
    monkeypatch.setattr(
        postgresql_module.tracemalloc,
        "get_traced_memory",
        lambda: next(memory_snapshots),
    )
    monkeypatch.setattr(
        postgresql_module.time,
        "perf_counter",
        lambda: next(perf_values),
    )

    await client._close_pool_with_metrics(pool, "maintenance-window")

    assert pool.closed is True
    record = next(
        rec
        for rec in caplog.records
        if "PostgreSQL pool teardown (maintenance-window)" in rec.message
    )
    assert "duration=0.1250s" in record.message
    assert "connections=4" in record.message
    assert "memory_before=4096" in record.message
    assert "memory_after=1024" in record.message


@pytest.mark.anyio
async def test_close_pool_with_metrics_estimates_holder_count(monkeypatch, caplog):
    caplog.set_level("INFO", logger="src.core.database.postgresql_client")
    client = PostgreSQLClient()

    class SaturatedPool:
        def __init__(self):
            self._holders = [object()] * 7
            self.closed = False

        async def close(self):
            self.closed = True

    pool = SaturatedPool()

    perf_values = iter([5.0, 5.032])
    monkeypatch.setattr(
        postgresql_module.tracemalloc,
        "is_tracing",
        lambda: False,
    )
    monkeypatch.setattr(
        postgresql_module.time,
        "perf_counter",
        lambda: next(perf_values),
    )

    await client._close_pool_with_metrics(pool, "saturation-recovery")

    assert pool.closed is True
    record = next(
        rec
        for rec in caplog.records
        if "PostgreSQL pool teardown (saturation-recovery)" in rec.message
    )
    assert "connections=7" in record.message
    assert "memory_before=n/a" in record.message
    assert "memory_after=n/a" in record.message


@pytest.mark.anyio
async def test_disconnect_invokes_teardown_metrics(monkeypatch):
    client = PostgreSQLClient()
    pool = _InitFailurePool()
    client.pool = pool

    original = PostgreSQLClient._close_pool_with_metrics
    reasons = []

    async def recorder(self, target_pool, reason):
        reasons.append(reason)
        await original(self, target_pool, reason)

    monkeypatch.setattr(PostgreSQLClient, "_close_pool_with_metrics", recorder)

    await client.disconnect()

    assert reasons == ["disconnect"]
    assert pool.closed is True
    assert client.pool is None


@pytest.mark.anyio
async def test_connect_partial_migration_failure_rolls_back(monkeypatch, caplog):
    caplog.set_level("WARNING", logger="src.core.database.postgresql_client")

    pools = []
    init_calls = 0

    async def fake_create_pool(*_args, **_kwargs):
        pool = _InitFailurePool()
        pools.append(pool)
        return pool

    async def fake_initialize(self):
        nonlocal init_calls
        init_calls += 1
        if init_calls == 1:
            raise RuntimeError("migration step 3/5 crashed")

    original = PostgreSQLClient._close_pool_with_metrics
    teardown_reasons = []

    async def recorder(self, pool, reason):
        teardown_reasons.append(reason)
        await original(self, pool, reason)

    monkeypatch.setattr(
        postgresql_module.asyncpg,
        "create_pool",
        fake_create_pool,
    )
    monkeypatch.setattr(PostgreSQLClient, "_initialize_tables", fake_initialize)
    monkeypatch.setattr(PostgreSQLClient, "_close_pool_with_metrics", recorder)

    client = PostgreSQLClient()
    client.config.connection_max_retries = 3
    client.config.connection_retry_backoff_seconds = 0

    await client.connect()

    assert len(pools) == 2
    assert pools[0].closed is True
    assert pools[1].closed is False
    assert client.pool is pools[1]
    assert teardown_reasons == ["init-failure"]
    assert any(
        "rolling back pending migrations" in record.message
        for record in caplog.records
    )


@pytest.mark.anyio
async def test_connect_pool_exhaustion_recovers(monkeypatch, caplog):
    caplog.set_level("INFO", logger="src.core.database.postgresql_client")

    exhaustion_pool = _InitFailurePool()
    healthy_pool = _InitFailurePool()
    attempts = []

    async def fake_create_pool(*_args, **_kwargs):
        attempt = len(attempts)
        attempts.append(attempt)
        if attempt == 0:
            exhaustion_pool.total_connections = 20
            raise RuntimeError("pool exhausted")
        return healthy_pool

    monkeypatch.setattr(
        postgresql_module.asyncpg,
        "create_pool",
        fake_create_pool,
    )

    original = PostgreSQLClient._close_pool_with_metrics
    teardown_reasons = []

    async def recorder(self, pool, reason):
        teardown_reasons.append((pool, reason))
        if pool is healthy_pool:
            await original(self, pool, reason)

    monkeypatch.setattr(PostgreSQLClient, "_close_pool_with_metrics", recorder)

    client = PostgreSQLClient()
    client.config.connection_max_retries = 2
    client.config.connection_retry_backoff_seconds = 0

    await client.connect()

    assert attempts == [0, 1]
    assert client.pool is healthy_pool
    assert teardown_reasons == []
    assert any(
        "Database connection attempt 1/2 failed" in record.message
        for record in caplog.records
    )
