"""Integration-style tests for the E2B sandbox manager."""

import logging

import pytest

from src.core.e2b import sandbox_manager as sandbox_module
from src.core.e2b.sandbox_manager import E2BSandboxManager, SandboxConfig

pytestmark = pytest.mark.anyio("asyncio")


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
