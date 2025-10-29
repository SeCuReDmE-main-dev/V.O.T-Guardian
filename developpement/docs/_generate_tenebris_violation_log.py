import asyncio
import logging

from src.core.security.tenebris import (
    TenebrisProtocol,
    TenebrisViolationException,
)


async def _run_violation_scenario(
    protocol: TenebrisProtocol,
    label: str,
    logger: logging.Logger,
) -> None:
    try:
        async with protocol.execute_protocol(label):
            logger.info("%s ACTIVE_STATE %s", label, protocol._active_sessions)
    except TenebrisViolationException as exc:
        logger.error("%s VIOLATION %s", label, exc)
        logger.error(
            "%s STATUS %s",
            label,
            protocol.get_protocol_status(label),
        )
        logger.error("%s SESSIONS %s", label, protocol._active_sessions)
    else:
        logger.warning("%s completed without violation", label)


async def main() -> None:
    logger = logging.getLogger("tenebris.diagnostics")
    logger.handlers = []
    handler = logging.FileHandler(
        "docs/samples_tenebris_violation.log",
        mode="w",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Scenario 1: sandbox already destroyed when cleanup runs
    protocol_destroyed = TenebrisProtocol()

    async def destroyed_sandbox(session_id: str) -> None:
        logger.warning("sandbox already destroyed for %s", session_id)
        raise RuntimeError("sandbox already destroyed")

    protocol_destroyed._destroy_e2b_sandbox = destroyed_sandbox
    await _run_violation_scenario(
        protocol_destroyed,
        "violation-sandbox",
        logger,
    )

    # Scenario 2: unauthorized access on key revocation
    protocol_key = TenebrisProtocol()

    async def unauthorized_key(session_id: str) -> None:
        logger.error(
            "unauthorized key access during revoke for %s",
            session_id,
        )
        raise PermissionError("unauthorized key access")

    protocol_key._revoke_crypto_keys = unauthorized_key
    await _run_violation_scenario(protocol_key, "violation-key", logger)


if __name__ == "__main__":
    asyncio.run(main())
