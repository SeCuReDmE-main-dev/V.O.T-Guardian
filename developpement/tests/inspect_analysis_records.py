"""Utility script to inspect recent analysis persistence records."""

import asyncio
import json
import os
from typing import Any, Dict

import asyncpg

DEFAULT_DB_URL = (
    "postgresql://vot_user:vot_password@localhost:5432/vot_guardian"
)


def _format_row(row: asyncpg.Record) -> str:
    mapped: Dict[str, Any] = dict(row)
    return json.dumps(mapped, default=str, indent=2, sort_keys=True)


async def main() -> None:
    database_url = os.getenv("POSTGRESQL_URL", DEFAULT_DB_URL)
    conn = await asyncpg.connect(database_url)
    try:
        analyses = await conn.fetch(
            """
         SELECT call_id,
             prediction,
             confidence,
             features,
             processing_time_ms,
             created_at
            FROM analysis_results
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        audits = await conn.fetch(
            """
            SELECT event_type, call_id, session_id, metadata, created_at
            FROM audit_trail
            ORDER BY created_at DESC
            LIMIT 5
            """
        )

        print("=== analysis_results (latest 5) ===")
        if analyses:
            for record in analyses:
                print(_format_row(record))
        else:
            print("<empty>")

        print("\n=== audit_trail (latest 5) ===")
        if audits:
            for record in audits:
                print(_format_row(record))
        else:
            print("<empty>")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
