"""
PostgreSQL Client - Database Operations
=======================================

Handles database operations for V.O.T. Guardian.

Features:
- Analysis results storage
- Audit trail management
- Compliance reporting
- Connection pooling

Author: Jean-Sébastien Beaulieu
"""

import asyncio
import json
import logging
import os
import time
import tracemalloc
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import asyncpg


    min_connections: int = 5
    max_connections: int = 20
    command_timeout: int = 60
    server_settings: Dict[str, str] = None
    connection_max_retries: int = 3
    connection_retry_backoff_seconds: float = 0.5


class PostgreSQLClient:
    """
    PostgreSQL client for V.O.T. Guardian database operations.
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or self._load_config()
        self.logger = logging.getLogger(__name__)
        self.pool: Optional[asyncpg.Pool] = None

    def _load_config(self) -> DatabaseConfig:
        """Load configuration from environment."""
        default_url = (
            'postgresql://vot_user:vot_password@localhost:5432/'
            'vot_guardian'
        )
        return DatabaseConfig(
            url=os.getenv('POSTGRESQL_URL', default_url),
            min_connections=int(os.getenv('DB_MIN_CONNECTIONS', '5')),
            max_connections=int(os.getenv('DB_MAX_CONNECTIONS', '20')),
            connection_max_retries=int(
                os.getenv('DB_CONNECTION_MAX_RETRIES', '3')
            ),
            connection_retry_backoff_seconds=float(
                os.getenv('DB_CONNECTION_BACKOFF_SECONDS', '0.5')
            ),
        )

    async def connect(self):
        """Create database connection pool."""
        attempts = max(1, self.config.connection_max_retries)
        backoff = max(0.0, self.config.connection_retry_backoff_seconds)
        last_error: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            try:
                pool = await asyncpg.create_pool(
                    self.config.url,
                    min_size=self.config.min_connections,
                    max_size=self.config.max_connections,
                    command_timeout=self.config.command_timeout,
                    server_settings=self.config.server_settings or {}
                )

                self.pool = pool

                try:
                    await self._initialize_tables()
                except Exception:
                    await pool.close()
                    self.pool = None
                    raise

                self.logger.info(
                    "Connected to PostgreSQL database (attempt %s/%s)",
                import time
                import tracemalloc
                    attempt,
                    attempts,
                )
                return

            except Exception as exc:
                last_error = exc
                if attempt < attempts:
                    self.logger.warning(
                            pool = None
                            try:
                                pool = await asyncpg.create_pool(
                                    self.config.url,
                                    min_size=self.config.min_connections,
                                    max_size=self.config.max_connections,
                                    command_timeout=self.config.command_timeout,
                                    server_settings=self.config.server_settings or {}
                                )

                                self.pool = pool

                                try:
                                    await self._initialize_tables()
                                except Exception as init_exc:
                                    self.logger.warning(
                                        "Database initialization failed, rolling back pending migrations: %s",
                                        init_exc,
                                    )
                                    await self._close_pool_with_metrics(pool, "init-failure")
                                    self.pool = None
                                    raise init_exc

                                self.logger.info(
                                    "Connected to PostgreSQL database (attempt %s/%s)",
                                    attempt,
                                    attempts,
                                )
                                return

                            except Exception as exc:
                                last_error = exc
                                if attempt < attempts:
                                    self.logger.warning(
                                        "Database connection attempt %s/%s failed: %s",
                                        attempt,
                                        attempts,
                                        exc,
                                    )
                                    await asyncio.sleep(backoff * attempt)
                                else:
                                    self.logger.error(
                                        "Failed to connect to database after %s attempts: %s",
                                        attempts,
                                        exc,
                                    )
                                if pool is not None and pool is self.pool:
                                    self.pool = None
                                if pool is not None:
                                    try:
                                        await self._close_pool_with_metrics(pool, "failure")
                                    except Exception:
                                        pass
                    ON analysis_results(call_id);
                CREATE INDEX IF NOT EXISTS idx_analysis_results_created_at
                    ON analysis_results(created_at);
                CREATE INDEX IF NOT EXISTS idx_analysis_results_prediction
                    ON analysis_results(prediction);
                """
            )

                            await self._close_pool_with_metrics(self.pool, "disconnect")
                            self.pool = None
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(100) NOT NULL,
                    call_id VARCHAR(255),
                    session_id VARCHAR(255),
                    metadata JSONB,

                    def _sample_memory_usage(self) -> Optional[int]:
                        """Return current traced memory if tracemalloc is active."""
                        if tracemalloc.is_tracing():
                            current, _ = tracemalloc.get_traced_memory()
                            return current
                        return None

                    def _estimate_pool_connections(self, pool: Any) -> Optional[int]:
                        """Best-effort estimation of active connections for logging."""
                        for attr in ("connection_count", "total_connections"):
                            value = getattr(pool, attr, None)
                            if isinstance(value, int):
                                return value
                        holders = getattr(pool, "_holders", None)
                        if isinstance(holders, list):
                            return len(holders)
                        return None

                    def _log_pool_teardown_metrics(
                        self,
                        reason: str,
                        duration: float,
                        connections: Optional[int],
                        memory_before: Optional[int],
                        memory_after: Optional[int],
                    ) -> None:
                        """Emit metrics about pool teardown for observability."""
                        self.logger.info(
                            (
                                "PostgreSQL pool teardown (%s): duration=%.4fs connections=%s "
                                "memory_before=%s memory_after=%s"
                            ),
                            reason,
                            duration,
                            connections if connections is not None else "unknown",
                            memory_before if memory_before is not None else "n/a",
                            memory_after if memory_after is not None else "n/a",
                        )

                    async def _close_pool_with_metrics(self, pool: Any, reason: str) -> None:
                        """Close the given pool while emitting teardown metrics."""
                        memory_before = self._sample_memory_usage()
                        connections = self._estimate_pool_connections(pool)
                        start = time.perf_counter()
                        try:
                            await pool.close()
                        finally:
                            duration = time.perf_counter() - start
                            memory_after = self._sample_memory_usage()
                            self._log_pool_teardown_metrics(
                                reason,
                                duration,
                                connections,
                                memory_before,
                                memory_after,
                            )
                    compliance_status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_audit_trail_call_id
                    ON audit_trail(call_id);
                CREATE INDEX IF NOT EXISTS idx_audit_trail_event_type
                    ON audit_trail(event_type);
                CREATE INDEX IF NOT EXISTS idx_audit_trail_created_at
                    ON audit_trail(created_at);
                """
            )

            # Model performance table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS model_performance (
                    id SERIAL PRIMARY KEY,
                    model_version VARCHAR(50) NOT NULL,
                    prediction_count INTEGER DEFAULT 0,
                    accuracy DECIMAL(5,4),
                    drift_score DECIMAL(5,4),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_model_performance_version
                    ON model_performance(model_version);
                CREATE INDEX IF NOT EXISTS idx_model_performance_created_at
                    ON model_performance(created_at);
                """
            )

    async def store_analysis_result(self, result: Dict[str, Any]):
        """Store analysis result in database."""
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        """
                        INSERT INTO analysis_results (
                            call_id,
                            prediction,
                            confidence,
                            features,
                            processing_time_ms
                        )
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (call_id) DO UPDATE SET
                            prediction = EXCLUDED.prediction,
                            confidence = EXCLUDED.confidence,
                            features = EXCLUDED.features,
                            processing_time_ms = EXCLUDED.processing_time_ms
                        """,
                        result['call_id'],
                        result['prediction'],
                        result['confidence'],
                        result.get('features'),
                        result.get('processing_time_ms'),
                    )

        except Exception as e:
            self.logger.error(f"Error storing analysis result: {e}")
            raise

    async def get_analysis_result(
        self,
        call_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve analysis result from database."""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM analysis_results WHERE call_id = $1
                """, call_id)

                if row:
                    features = row['features']
                    if isinstance(features, str):
                        try:
                            features = json.loads(features)
                        except json.JSONDecodeError:
                            self.logger.debug(
                                "Failed to decode features JSON for call %s",
                                row['call_id'],
                            )

                    processing_time = row['processing_time_ms']
                    if processing_time is not None:
                        processing_time = float(processing_time)

                    return {
                        'id': row['id'],
                        'call_id': row['call_id'],
                        'prediction': row['prediction'],
                        'confidence': float(row['confidence']),
                        'features': features,
                        'processing_time_ms': processing_time,
                        'created_at': row['created_at'].isoformat(),
                    }

        except Exception as e:
            self.logger.error(f"Error retrieving analysis result: {e}")

        return None

    async def log_audit_event(
        self,
        event_type: str,
        call_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """Log audit event to database."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_trail (
                        event_type,
                        call_id,
                        session_id,
                        metadata,
                        compliance_status
                    )
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    event_type,
                    call_id,
                    session_id,
                    metadata or {},
                    'COMPLIANT',
                )

        except Exception as e:
            self.logger.error(f"Error logging audit event: {e}")
            raise

    async def get_compliance_report(
        self,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Generate compliance report for audit purposes."""
        try:
            async with self.pool.acquire() as conn:
                # Get analysis statistics
                analysis_stats = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) AS total_analyses,
                        COUNT(
                            CASE WHEN prediction = 'AI' THEN 1 END
                        ) AS ai_predictions,
                        COUNT(
                            CASE WHEN prediction = 'HUMAN' THEN 1 END
                        ) AS human_predictions,
                        AVG(confidence) AS avg_confidence,
                        AVG(processing_time_ms) AS avg_processing_time
                    FROM analysis_results
                    WHERE created_at BETWEEN $1 AND $2
                    """,
                    start_date,
                    end_date,
                )

                # Get audit statistics
                audit_stats = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) AS total_events,
                        COUNT(
                            CASE WHEN compliance_status = 'COMPLIANT'
                            THEN 1 END
                        ) AS compliant_events,
                        COUNT(
                            CASE WHEN compliance_status = 'DEGRADED'
                            THEN 1 END
                        ) AS degraded_events
                    FROM audit_trail
                    WHERE created_at BETWEEN $1 AND $2
                    """,
                    start_date,
                    end_date,
                )

                avg_confidence = analysis_stats['avg_confidence'] or 0
                avg_processing = analysis_stats['avg_processing_time'] or 0

                total_events = audit_stats['total_events'] or 0
                compliant_events = audit_stats['compliant_events'] or 0
                compliance_rate = 100
                if total_events > 0:
                    compliance_rate = (compliant_events / total_events) * 100

                analysis_summary = {
                    'total': analysis_stats['total_analyses'],
                    'ai_predictions': analysis_stats['ai_predictions'],
                    'human_predictions': analysis_stats['human_predictions'],
                    'average_confidence': float(avg_confidence),
                    'average_processing_time_ms': float(avg_processing),
                }

                audit_summary = {
                    'total_events': total_events,
                    'compliant_events': compliant_events,
                    'degraded_events': audit_stats['degraded_events'] or 0,
                    'compliance_rate': compliance_rate,
                }

                return {
                    'period': {'start': start_date, 'end': end_date},
                    'analysis': analysis_summary,
                    'audit': audit_summary,
                    'generated_at': datetime.utcnow().isoformat(),
                }

        except Exception as e:
            self.logger.error(f"Error generating compliance report: {e}")
            return {'error': str(e)}

    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        try:
            async with self.pool.acquire() as conn:
                # Get recent performance data
                metrics = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_analyses_24h,
                        AVG(processing_time_ms) as avg_latency_24h,
                        MIN(created_at) as first_analysis,
                        MAX(created_at) as last_analysis
                    FROM analysis_results
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                """)

                avg_latency = metrics['avg_latency_24h'] or 0

                return {
                    'total_analyses_24h': metrics['total_analyses_24h'],
                    'average_latency_24h_ms': float(avg_latency),
                    'uptime_hours': 24,  # Would calculate actual uptime
                    'database_status': 'healthy'
                }

        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {'error': str(e)}
