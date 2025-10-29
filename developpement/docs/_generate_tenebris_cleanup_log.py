import asyncio
import logging

from src.core.security.tenebris import TenebrisConfig, TenebrisProtocol


async def main() -> None:
    logger = logging.getLogger("src.core.security.tenebris")
    logger.handlers = []
    handler = logging.FileHandler(
        "docs/samples_tenebris_cleanup.log",
        mode="w",
    )
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    protocol = TenebrisProtocol()
    async with protocol.execute_protocol("diagnostic-success"):
        logger.info("ACTIVE_SESSION_ENCRYPTED %s", protocol._active_sessions)
    logger.info("POST_CLEANUP_ENCRYPTED %s", protocol._active_sessions)

    protocol_no_crypto = TenebrisProtocol(
        TenebrisConfig(encryption_enabled=False)
    )
    async with protocol_no_crypto.execute_protocol("diagnostic-no-crypto"):
        logger.info(
            "ACTIVE_SESSION_NO_ENCRYPTION %s",
            protocol_no_crypto._active_sessions,
        )
    logger.info(
        "POST_CLEANUP_NO_ENCRYPTION %s",
        protocol_no_crypto._active_sessions,
    )


if __name__ == "__main__":
    asyncio.run(main())
