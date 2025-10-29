"""Integration-style tests for the E2B sandbox manager."""

import asyncio
import logging
import types

import pytest

from src.core.e2b import sandbox_manager as sandbox_module
from src.core.e2b.sandbox_manager import (
    E2BSandboxManager,
    SandboxConfig,
    SandboxInstance,
)


@pytest.fixture
def anyio_backend():
    """Force anyio tests to execute with the asyncio backend only."""
    return "asyncio"


@pytest.mark.anyio
async def test_sandbox_lifecycle_happy_path(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="src.core.e2b.sandbox_manager")

    created_kwargs = []
    destroyed_ids = []

    class StubSandbox:
        counter = 0

        def __init__(self, sandbox_id: str):
            self.id = sandbox_id
            self.kill_called = False

        @classmethod
        def create(cls, **kwargs):  # pragma: no cover - exercised in test
            cls.counter += 1
            created_kwargs.append(kwargs)
            return cls(f"stub-{cls.counter}")

        def kill(self):  # pragma: no cover - exercised in test
            self.kill_called = True
            destroyed_ids.append(self.id)

        def close(self):  # pragma: no cover - safety fallback
            destroyed_ids.append(f"close:{self.id}")

    monkeypatch.setattr(sandbox_module, "GenericSandbox", StubSandbox)
    monkeypatch.setattr(sandbox_module, "E2B_GENERIC_AVAILABLE", True)
    monkeypatch.setattr(sandbox_module, "CodeInterpreterSandbox", None)
    monkeypatch.setattr(sandbox_module, "E2B_CI_AVAILABLE", False)

    config = SandboxConfig(
        api_key="fake-api-key",
        min_pool_size=1,
        max_pool_size=2,
        sandbox_timeout=5,
        health_check_interval=1,
        max_concurrent_per_sandbox=1,
        template_id="tmpl-123",
    )

    manager = E2BSandboxManager(config=config)
    await manager.start()

    assert len(manager._pool) == 1
    assert created_kwargs == [{
        "template": "tmpl-123",
        "timeout": config.sandbox_timeout,
        "allow_internet_access": False,
        "api_key": "fake-api-key",
    }]

    async with manager.get_sandbox() as sandbox:
        assert sandbox.id == "stub-1"

    stats = manager.get_pool_stats()["stats"]
    assert stats["requests_served"] == 1
    assert stats["sandboxes_created"] == 1
    assert all(
        instance.active_connections == 0 for instance in manager._pool.values()
    )

    await manager.stop()

    post_stop_stats = manager.get_pool_stats()["stats"]
    assert post_stop_stats["sandboxes_destroyed"] == 1
    assert len(manager._pool) == 0
    assert destroyed_ids == ["stub-1"]

    assert any(
        "Created new E2B sandbox" in record.message
        for record in caplog.records
    )
    assert any(
        "Destroyed E2B sandbox" in record.message
        for record in caplog.records
    )


@pytest.mark.anyio
async def test_sandbox_creation_transient_failure_recovers(
    monkeypatch,
    caplog,
):
    caplog.set_level(logging.INFO, logger="src.core.e2b.sandbox_manager")

    class FlakySandbox:
        counter = 0
        failures = 2

        @classmethod
        def create(cls, **kwargs):
            if cls.failures > 0:
                cls.failures -= 1
                raise RuntimeError("transient network error")
            cls.counter += 1
            return types.SimpleNamespace(id=f"flaky-{cls.counter}")

    monkeypatch.setattr(sandbox_module, "GenericSandbox", FlakySandbox)
    monkeypatch.setattr(sandbox_module, "E2B_GENERIC_AVAILABLE", True)
    monkeypatch.setattr(sandbox_module, "CodeInterpreterSandbox", None)
    monkeypatch.setattr(sandbox_module, "E2B_CI_AVAILABLE", False)

    config = SandboxConfig(
        api_key="fake",
        min_pool_size=0,
        max_pool_size=2,
        sandbox_timeout=5,
        health_check_interval=1,
        max_concurrent_per_sandbox=1,
        template_id="tmpl-456",
        creation_max_retries=3,
        recovery_backoff_seconds=0,
    )

    manager = E2BSandboxManager(config=config)
    instance = await manager._create_sandbox()

    assert instance.id == "flaky-1"
    assert manager._stats["sandboxes_created"] == 1
    assert manager._stats["errors"] == 2
    assert any(
        "Sandbox creation failed" in record.message
        for record in caplog.records
    )
    assert any(
        "Recovered E2B sandbox creation" in record.message
        for record in caplog.records
    )


@pytest.mark.anyio
async def test_sandbox_creation_retry_exhaustion_logs_error(
    monkeypatch,
    caplog,
):
    caplog.set_level(logging.ERROR, logger="src.core.e2b.sandbox_manager")

    class DeadSandbox:
        @classmethod
        def create(cls, **kwargs):
            raise RuntimeError("quota hard fail")

    monkeypatch.setattr(sandbox_module, "GenericSandbox", DeadSandbox)
    monkeypatch.setattr(sandbox_module, "E2B_GENERIC_AVAILABLE", True)
    monkeypatch.setattr(sandbox_module, "CodeInterpreterSandbox", None)
    monkeypatch.setattr(sandbox_module, "E2B_CI_AVAILABLE", False)

    config = SandboxConfig(
        api_key="fake",
        min_pool_size=0,
        max_pool_size=1,
        sandbox_timeout=5,
        health_check_interval=1,
        max_concurrent_per_sandbox=1,
        template_id="tmpl-789",
        creation_max_retries=2,
        recovery_backoff_seconds=0,
    )

    manager = E2BSandboxManager(config=config)

    with pytest.raises(RuntimeError, match="quota hard fail"):
        await manager._create_sandbox()

    assert manager._stats["errors"] == 2
    assert any(
        "Sandbox creation exhausted retries" in record.message
        for record in caplog.records
    )


@pytest.mark.anyio
async def test_dead_sandbox_replaced_during_scale(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="src.core.e2b.sandbox_manager")

    destroy_calls = []

    class SimpleSandbox:
        counter = 0

        @classmethod
        def create(cls, **kwargs):
            cls.counter += 1
            return types.SimpleNamespace(id=f"sb-{cls.counter}")

    def kill_stub():
        destroy_calls.append("kill")

    monkeypatch.setattr(sandbox_module, "GenericSandbox", SimpleSandbox)
    monkeypatch.setattr(sandbox_module, "E2B_GENERIC_AVAILABLE", True)
    monkeypatch.setattr(sandbox_module, "CodeInterpreterSandbox", None)
    monkeypatch.setattr(sandbox_module, "E2B_CI_AVAILABLE", False)

    config = SandboxConfig(
        api_key="fake",
        min_pool_size=1,
        max_pool_size=2,
        sandbox_timeout=5,
        health_check_interval=1,
        max_concurrent_per_sandbox=1,
        template_id="tmpl-990",
        creation_max_retries=1,
        recovery_backoff_seconds=0,
    )

    manager = E2BSandboxManager(config=config)
    manager._pool = {
        "sb-old": SandboxInstance(
            id="sb-old",
            sandbox=types.SimpleNamespace(kill=kill_stub),
            created_at=0.0,
            last_used=0.0,
            active_connections=0,
            status='dead',
        )
    }

    await manager._destroy_sandbox("sb-old")
    await manager._scale_pool(0)

    assert destroy_calls == ["kill"]
    assert manager._stats["sandboxes_destroyed"] == 1
    assert manager.get_pool_stats()["total_sandboxes"] == 1
    new_id = next(iter(manager._pool.keys()))
    assert new_id.startswith("sb-")
    assert any(
        "Destroyed E2B sandbox" in record.message
        for record in caplog.records
    )
    assert any(
        "Created new E2B sandbox" in record.message
        for record in caplog.records
    )


@pytest.mark.anyio
async def test_sandbox_creation_quota_error(monkeypatch, caplog):
    caplog.set_level(logging.ERROR, logger="src.core.e2b.sandbox_manager")

    class QuotaSandbox:
        @classmethod
        def create(cls, **kwargs):  # pragma: no cover - exercised in test
            raise RuntimeError("quota exceeded")

    monkeypatch.setattr(sandbox_module, "GenericSandbox", QuotaSandbox)
    monkeypatch.setattr(sandbox_module, "E2B_GENERIC_AVAILABLE", True)
    monkeypatch.setattr(sandbox_module, "CodeInterpreterSandbox", None)
    monkeypatch.setattr(sandbox_module, "E2B_CI_AVAILABLE", False)

    config = SandboxConfig(
        api_key="fake-api-key",
        min_pool_size=0,
        max_pool_size=1,
        sandbox_timeout=5,
        health_check_interval=1,
        max_concurrent_per_sandbox=1,
        template_id="tmpl-123",
    )

    manager = E2BSandboxManager(config=config)

    with pytest.raises(RuntimeError, match="quota exceeded"):
        await manager._create_sandbox()

    stats = manager.get_pool_stats()["stats"]
    assert stats["errors"] == 1
    assert len(manager._pool) == 0
    assert any(
        "Failed to create E2B sandbox: quota exceeded" in record.message
        for record in caplog.records
    )


@pytest.mark.anyio
async def test_health_check_marks_degraded_and_logs(monkeypatch, caplog):
    caplog.set_level(logging.WARNING, logger="src.core.e2b.sandbox_manager")

    config = SandboxConfig(
        api_key="fake",
        min_pool_size=0,
        max_pool_size=3,
        sandbox_timeout=5,
        health_check_interval=1,
        max_concurrent_per_sandbox=1,
    )

    manager = E2BSandboxManager(config=config)

    slow_instance = SandboxInstance(
        id="sb-slow",
        sandbox=object(),
        created_at=0.0,
        last_used=0.0,
        active_connections=0,
        status='healthy',
    )
    fast_instance = SandboxInstance(
        id="sb-fast",
        sandbox=object(),
        created_at=0.0,
        last_used=0.0,
        active_connections=0,
        status='healthy',
    )

    manager._pool = {
        "sb-slow": slow_instance,
        "sb-fast": fast_instance,
    }

    time_values = iter([1000.0, 1006.5, 2000.0, 2000.0])

    def fake_time():
        return next(time_values, 2000.0)

    monkeypatch.setattr(
        sandbox_module,
        "time",
        types.SimpleNamespace(time=fake_time),
    )

    await manager._perform_health_checks()

    assert manager._pool["sb-slow"].status == 'degraded'
    assert manager._pool["sb-fast"].status == 'healthy'
    assert any(
        "response degraded" in record.message for record in caplog.records
    )

    stats = manager.get_pool_stats()
    assert stats["degraded"] == 1


@pytest.mark.anyio
async def test_acquire_sandbox_logs_pool_exhaustion(caplog):
    caplog.set_level(logging.ERROR, logger="src.core.e2b.sandbox_manager")

    config = SandboxConfig(
        api_key="fake",
        min_pool_size=0,
        max_pool_size=1,
        sandbox_timeout=5,
        health_check_interval=1,
        max_concurrent_per_sandbox=1,
    )

    manager = E2BSandboxManager(config=config)
    manager._pool = {
        "sb-1": SandboxInstance(
            id="sb-1",
            sandbox=object(),
            created_at=0.0,
            last_used=0.0,
            active_connections=1,
            status='healthy',
        )
    }

    with pytest.raises(Exception, match="Sandbox pool exhausted"):
        await manager._acquire_sandbox()

    assert any(
        "Sandbox pool exhausted" in record.message for record in caplog.records
    )


@pytest.mark.anyio
async def test_scale_pool_trims_idle_sandboxes(caplog):
    caplog.set_level(logging.INFO, logger="src.core.e2b.sandbox_manager")

    destroyed = []

    class KillableSandbox:
        def __init__(self, name: str):
            self.name = name

        def kill(self):
            destroyed.append(self.name)

    config = SandboxConfig(
        api_key="fake",
        min_pool_size=1,
        max_pool_size=10,
        sandbox_timeout=5,
        health_check_interval=1,
        max_concurrent_per_sandbox=1,
    )

    manager = E2BSandboxManager(config=config)

    manager._pool = {
        f"sb-{idx}": SandboxInstance(
            id=f"sb-{idx}",
            sandbox=KillableSandbox(f"sb-{idx}"),
            created_at=0.0,
            last_used=0.0,
            active_connections=0,
            status='healthy',
        )
        for idx in range(1, 8)
    }

    await manager._scale_pool(healthy_count=7)

    assert len(manager._pool) == 5
    assert destroyed == ["sb-1", "sb-2"]
    assert manager._stats["sandboxes_destroyed"] == 2
    assert any(
        "Destroyed E2B sandbox" in record.message for record in caplog.records
    )


@pytest.mark.anyio
async def test_health_check_loop_cycles_and_logs(monkeypatch, caplog):
    caplog.set_level(logging.ERROR, logger="src.core.e2b.sandbox_manager")

    config = SandboxConfig(
        api_key="fake",
        min_pool_size=0,
        max_pool_size=1,
        sandbox_timeout=5,
        health_check_interval=1,
        max_concurrent_per_sandbox=1,
    )

    manager = E2BSandboxManager(config=config)

    events = []
    sleep_calls = 0
    real_sleep = asyncio.sleep

    async def fake_perform():
        events.append("tick")
        if len(events) == 2:
            raise RuntimeError("synthetic health failure")

    async def fake_sleep(_interval):
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls >= 4:
            raise asyncio.CancelledError()
        await real_sleep(0)

    manager._perform_health_checks = fake_perform  # type: ignore[assignment]
    monkeypatch.setattr(sandbox_module.asyncio, "sleep", fake_sleep)

    task = asyncio.create_task(manager._health_check_loop())
    await real_sleep(0)
    await real_sleep(0)
    await task

    assert events == ["tick", "tick", "tick"]
    assert sleep_calls >= 3
    assert any(
        "Health check error: synthetic health failure" in record.message
        for record in caplog.records
    )


@pytest.mark.anyio
async def test_create_sandbox_uses_code_interpreter_when_generic_unavailable(
    monkeypatch,
    caplog,
):
    caplog.set_level(logging.INFO, logger="src.core.e2b.sandbox_manager")

    created_kwargs = []

    class CodeSandbox:
        counter = 0

        @classmethod
        def create(cls, **kwargs):
            cls.counter += 1
            created_kwargs.append(kwargs)

            def kill():
                return None

            return types.SimpleNamespace(
                id=f"ci-{cls.counter}",
                kill=kill,
            )

    monkeypatch.setattr(sandbox_module, "GenericSandbox", None)
    monkeypatch.setattr(sandbox_module, "E2B_GENERIC_AVAILABLE", False)
    monkeypatch.setattr(sandbox_module, "CodeInterpreterSandbox", CodeSandbox)
    monkeypatch.setattr(sandbox_module, "E2B_CI_AVAILABLE", True)

    manager = E2BSandboxManager(
        config=SandboxConfig(
            api_key="ci-key",
            min_pool_size=0,
            max_pool_size=1,
            sandbox_timeout=10,
            health_check_interval=1,
            max_concurrent_per_sandbox=1,
        )
    )

    instance = await manager._create_sandbox()

    assert instance.id == "ci-1"
    assert created_kwargs == [{
        "allow_internet_access": False,
        "timeout": 10,
        "api_key": "ci-key",
    }]
    assert any(
        "Created new E2B sandbox" in record.message
        for record in caplog.records
    )


@pytest.mark.anyio
async def test_scale_pool_trims_heterogeneous_templates(caplog):
    caplog.set_level(logging.INFO, logger="src.core.e2b.sandbox_manager")

    destroyed = []

    def make_sandbox(name: str):
        def kill():
            destroyed.append(name)

        return types.SimpleNamespace(kill=kill)

    config = SandboxConfig(
        api_key="fake",
        min_pool_size=2,
        max_pool_size=10,
        sandbox_timeout=5,
        health_check_interval=1,
        max_concurrent_per_sandbox=1,
    )

    manager = E2BSandboxManager(config=config)

    manager._pool = {
        "audio-1": SandboxInstance(
            id="audio-1",
            sandbox=make_sandbox("audio-1"),
            created_at=0.0,
            last_used=0.0,
            active_connections=0,
            status='healthy',
        ),
        "ml-1": SandboxInstance(
            id="ml-1",
            sandbox=make_sandbox("ml-1"),
            created_at=0.0,
            last_used=0.0,
            active_connections=0,
            status='healthy',
        ),
        "ci-1": SandboxInstance(
            id="ci-1",
            sandbox=make_sandbox("ci-1"),
            created_at=0.0,
            last_used=0.0,
            active_connections=1,
            status='healthy',
        ),
        "audio-2": SandboxInstance(
            id="audio-2",
            sandbox=make_sandbox("audio-2"),
            created_at=0.0,
            last_used=0.0,
            active_connections=0,
            status='degraded',
        ),
        "ml-2": SandboxInstance(
            id="ml-2",
            sandbox=make_sandbox("ml-2"),
            created_at=0.0,
            last_used=0.0,
            active_connections=0,
            status='healthy',
        ),
        "ci-2": SandboxInstance(
            id="ci-2",
            sandbox=make_sandbox("ci-2"),
            created_at=0.0,
            last_used=0.0,
            active_connections=0,
            status='healthy',
        ),
        "audio-3": SandboxInstance(
            id="audio-3",
            sandbox=make_sandbox("audio-3"),
            created_at=0.0,
            last_used=0.0,
            active_connections=0,
            status='healthy',
        ),
        "ci-active": SandboxInstance(
            id="ci-active",
            sandbox=make_sandbox("ci-active"),
            created_at=0.0,
            last_used=0.0,
            active_connections=2,
            status='healthy',
        ),
    }

    await manager._scale_pool(healthy_count=8)

    assert destroyed == ["audio-1", "ml-1"]
    assert "audio-1" not in manager._pool
    assert "ml-1" not in manager._pool
    assert "ci-1" in manager._pool
    assert "ci-active" in manager._pool
    assert manager._stats["sandboxes_destroyed"] == 2
    assert any(
        "Destroyed E2B sandbox" in record.message
        for record in caplog.records
    )
