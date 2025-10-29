""""""

PostgreSQL Client - Database OperationsPostgreSQL Client - Database Operations

==============================================================================



Handles database operations for V.O.T. Guardian.Handles database operations for V.O.T. Guardian.

- Analysis results storage- Analysis results storage

- Audit trail management- Audit trail management

- Compliance reporting- Compliance reporting

- Connection pooling- Connection pooling



Author: Jean-Sébastien BeaulieuAuthor: Jean-Sébastien Beaulieu

""""""



from __future__ import annotationsimport asyncio

import json

import asyncioimport logging

import jsonimport os

import loggingimport time

import osimport tracemalloc

import timefrom dataclasses import dataclass

import tracemallocfrom datetime import datetime

from dataclasses import dataclassfrom typing import Any, Dict, Optional

from datetime import datetime

from typing import Any, Dict, Optionalimport asyncpg



import asyncpg

    min_connections: int = 5

    max_connections: int = 20

@dataclass    command_timeout: int = 60

class DatabaseConfig:    server_settings: Dict[str, str] = None

    """Configuration for PostgreSQL database."""    connection_max_retries: int = 3

    connection_retry_backoff_seconds: float = 0.5

    url: str

    min_connections: int = 5

    max_connections: int = 20class PostgreSQLClient:

    command_timeout: int = 60    """

    server_settings: Optional[Dict[str, str]] = None    PostgreSQL client for V.O.T. Guardian database operations.

    connection_max_retries: int = 3    """

    connection_retry_backoff_seconds: float = 0.5

    def __init__(self, config: Optional[DatabaseConfig] = None):

        self.config = config or self._load_config()

class PostgreSQLClient:        self.logger = logging.getLogger(__name__)

    """PostgreSQL client for V.O.T. Guardian database operations."""        self.pool: Optional[asyncpg.Pool] = None



    def __init__(self, config: Optional[DatabaseConfig] = None):    def _load_config(self) -> DatabaseConfig:

        self.config = config or self._load_config()        """Load configuration from environment."""

        self.logger = logging.getLogger(__name__)        default_url = (

        self.pool: Optional[asyncpg.Pool] = None            'postgresql://vot_user:vot_password@localhost:5432/'

            'vot_guardian'

    def _load_config(self) -> DatabaseConfig:        )

        """Load configuration from environment."""        return DatabaseConfig(

        default_url = (            url=os.getenv('POSTGRESQL_URL', default_url),

            "postgresql://vot_user:vot_password@localhost:5432/"            min_connections=int(os.getenv('DB_MIN_CONNECTIONS', '5')),

            "vot_guardian"            max_connections=int(os.getenv('DB_MAX_CONNECTIONS', '20')),

        )            connection_max_retries=int(

        return DatabaseConfig(                os.getenv('DB_CONNECTION_MAX_RETRIES', '3')

            url=os.getenv("POSTGRESQL_URL", default_url),            ),

            min_connections=int(os.getenv("DB_MIN_CONNECTIONS", "5")),            connection_retry_backoff_seconds=float(

            max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "20")),                os.getenv('DB_CONNECTION_BACKOFF_SECONDS', '0.5')

            command_timeout=int(os.getenv("DB_COMMAND_TIMEOUT", "60")),            ),

            connection_max_retries=int(        )

                os.getenv("DB_CONNECTION_MAX_RETRIES", "3")

            ),    async def connect(self):

            connection_retry_backoff_seconds=float(        """Create database connection pool."""

                os.getenv("DB_CONNECTION_RETRY_BACKOFF_SECONDS", "0.5")        attempts = max(1, self.config.connection_max_retries)

            ),        backoff = max(0.0, self.config.connection_retry_backoff_seconds)

        )        last_error: Optional[Exception] = None



    async def connect(self) -> None:        for attempt in range(1, attempts + 1):

        """Create database connection pool."""            try:

        attempts = max(1, self.config.connection_max_retries)                pool = await asyncpg.create_pool(

        backoff = max(0.0, self.config.connection_retry_backoff_seconds)                    self.config.url,

        last_error: Optional[Exception] = None                    min_size=self.config.min_connections,

                    max_size=self.config.max_connections,

        for attempt in range(1, attempts + 1):                    command_timeout=self.config.command_timeout,

            pool: Optional[asyncpg.Pool] = None                    server_settings=self.config.server_settings or {}

            try:                )

                pool = await asyncpg.create_pool(

                    self.config.url,                self.pool = pool

                    min_size=self.config.min_connections,

                    max_size=self.config.max_connections,                try:

                    command_timeout=self.config.command_timeout,                    await self._initialize_tables()

                    server_settings=self.config.server_settings or {},                except Exception:

                )                    await pool.close()

                    self.pool = None

                self.pool = pool                    raise



                try:                self.logger.info(

                    await self._initialize_tables()                    "Connected to PostgreSQL database (attempt %s/%s)",

                except Exception as init_exc:                import time

                    self.logger.warning(                import tracemalloc

                        "Database initialization failed, rolling back pending migrations: %s",                    attempt,

                        init_exc,                    attempts,

                    )                )

                    await self._close_pool_with_metrics(pool, "init-failure")                return

                    self.pool = None

                    raise init_exc            except Exception as exc:

                last_error = exc

                self.logger.info(                if attempt < attempts:

                    "Connected to PostgreSQL database (attempt %s/%s)",                    self.logger.warning(

                    attempt,                            pool = None

                    attempts,                            try:

                )                                pool = await asyncpg.create_pool(

                return                                    self.config.url,

                                    min_size=self.config.min_connections,

            except Exception as exc:                                    max_size=self.config.max_connections,

                last_error = exc                                    command_timeout=self.config.command_timeout,

                if attempt < attempts:                                    server_settings=self.config.server_settings or {}

                    self.logger.warning(                                )

                        "Database connection attempt %s/%s failed: %s",

                        attempt,                                self.pool = pool

                        attempts,

                        exc,                                try:

                    )                                    await self._initialize_tables()

                    await asyncio.sleep(backoff * attempt)                                except Exception as init_exc:

                else:                                    self.logger.warning(

                    self.logger.error(                                        "Database initialization failed, rolling back pending migrations: %s",

                        "Failed to connect to database after %s attempts: %s",                                        init_exc,

                        attempts,                                    )

                        exc,                                    await self._close_pool_with_metrics(pool, "init-failure")

                    )                                    self.pool = None

                                    raise init_exc

                if pool is not None and pool is self.pool:

                    self.pool = None                                self.logger.info(

                if pool is not None:                                    "Connected to PostgreSQL database (attempt %s/%s)",

                    try:                                    attempt,

                        await self._close_pool_with_metrics(pool, "failure")                                    attempts,

                    except Exception:                                )

                        pass                                return



        if last_error is not None:                            except Exception as exc:

            raise last_error                                last_error = exc

        raise RuntimeError("Unable to establish PostgreSQL connection pool")                                if attempt < attempts:

                                    self.logger.warning(

    async def disconnect(self) -> None:                                        "Database connection attempt %s/%s failed: %s",

        """Close database connection pool."""                                        attempt,

        if self.pool:                                        attempts,

            await self._close_pool_with_metrics(self.pool, "disconnect")                                        exc,

            self.pool = None                                    )

            self.logger.info("Disconnected from PostgreSQL database")                                    await asyncio.sleep(backoff * attempt)

                                else:

    async def _initialize_tables(self) -> None:                                    self.logger.error(

        """Ensure required tables exist."""                                        "Failed to connect to database after %s attempts: %s",

        if not self.pool:                                        attempts,

            raise RuntimeError("Database pool is not initialized")                                        exc,

                                    )

        async with self.pool.acquire() as conn:                                if pool is not None and pool is self.pool:

            await conn.execute(                                    self.pool = None

                """                                if pool is not None:

                CREATE TABLE IF NOT EXISTS analysis_results (                                    try:

                    id SERIAL PRIMARY KEY,                                        await self._close_pool_with_metrics(pool, "failure")

                    call_id VARCHAR(255) UNIQUE NOT NULL,                                    except Exception:

                    prediction VARCHAR(50) NOT NULL,                                        pass

                    confidence DECIMAL(5,4) NOT NULL,                    ON analysis_results(call_id);

                    features JSONB,                CREATE INDEX IF NOT EXISTS idx_analysis_results_created_at

                    processing_time_ms DECIMAL(10,2),                    ON analysis_results(created_at);

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP                CREATE INDEX IF NOT EXISTS idx_analysis_results_prediction

                );                    ON analysis_results(prediction);

                """

                CREATE INDEX IF NOT EXISTS idx_analysis_results_call_id            )

                    ON analysis_results(call_id);

                CREATE INDEX IF NOT EXISTS idx_analysis_results_created_at                            await self._close_pool_with_metrics(self.pool, "disconnect")

                    ON analysis_results(created_at);                            self.pool = None

                CREATE INDEX IF NOT EXISTS idx_analysis_results_prediction            await conn.execute(

                    ON analysis_results(prediction);                """

                """                CREATE TABLE IF NOT EXISTS audit_trail (

            )                    id SERIAL PRIMARY KEY,

                    event_type VARCHAR(100) NOT NULL,

            await conn.execute(                    call_id VARCHAR(255),

                """                    session_id VARCHAR(255),

                CREATE TABLE IF NOT EXISTS audit_trail (                    metadata JSONB,

                    id SERIAL PRIMARY KEY,

                    event_type VARCHAR(100) NOT NULL,                    def _sample_memory_usage(self) -> Optional[int]:

                    call_id VARCHAR(255),                        """Return current traced memory if tracemalloc is active."""

                    session_id VARCHAR(255),                        if tracemalloc.is_tracing():

                    metadata JSONB,                            current, _ = tracemalloc.get_traced_memory()

                    compliance_status VARCHAR(50),                            return current

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP                        return None

                );

                    def _estimate_pool_connections(self, pool: Any) -> Optional[int]:

                CREATE INDEX IF NOT EXISTS idx_audit_trail_call_id                        """Best-effort estimation of active connections for logging."""

                    ON audit_trail(call_id);                        for attr in ("connection_count", "total_connections"):

                CREATE INDEX IF NOT EXISTS idx_audit_trail_event_type                            value = getattr(pool, attr, None)

                    ON audit_trail(event_type);                            if isinstance(value, int):

                CREATE INDEX IF NOT EXISTS idx_audit_trail_created_at                                return value

                    ON audit_trail(created_at);                        holders = getattr(pool, "_holders", None)

                """                        if isinstance(holders, list):

            )                            return len(holders)

                        return None

            await conn.execute(

                """                    def _log_pool_teardown_metrics(

                CREATE TABLE IF NOT EXISTS model_performance (                        self,

                    id SERIAL PRIMARY KEY,                        reason: str,

                    model_version VARCHAR(50) NOT NULL,                        duration: float,

                    prediction_count INTEGER DEFAULT 0,                        connections: Optional[int],

                    accuracy DECIMAL(5,4),                        memory_before: Optional[int],

                    drift_score DECIMAL(5,4),                        memory_after: Optional[int],

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP                    ) -> None:

                );                        """Emit metrics about pool teardown for observability."""

                        self.logger.info(

                CREATE INDEX IF NOT EXISTS idx_model_performance_version                            (

                    ON model_performance(model_version);                                "PostgreSQL pool teardown (%s): duration=%.4fs connections=%s "

                CREATE INDEX IF NOT EXISTS idx_model_performance_created_at                                "memory_before=%s memory_after=%s"

                    ON model_performance(created_at);                            ),

                """                            reason,

            )                            duration,

                            connections if connections is not None else "unknown",

    async def store_analysis_result(self, result: Dict[str, Any]) -> None:                            memory_before if memory_before is not None else "n/a",

        """Store analysis result in database."""                            memory_after if memory_after is not None else "n/a",

        if not self.pool:                        )

            raise RuntimeError("Database pool is not initialized")

                    async def _close_pool_with_metrics(self, pool: Any, reason: str) -> None:

        try:                        """Close the given pool while emitting teardown metrics."""

            async with self.pool.acquire() as conn:                        memory_before = self._sample_memory_usage()

                async with conn.transaction():                        connections = self._estimate_pool_connections(pool)

                    await conn.execute(                        start = time.perf_counter()

                        """                        try:

                        INSERT INTO analysis_results (                            await pool.close()

                            call_id,                        finally:

                            prediction,                            duration = time.perf_counter() - start

                            confidence,                            memory_after = self._sample_memory_usage()

                            features,                            self._log_pool_teardown_metrics(

                            processing_time_ms                                reason,

                        )                                duration,

                        VALUES ($1, $2, $3, $4, $5)                                connections,

                        ON CONFLICT (call_id) DO UPDATE SET                                memory_before,

                            prediction = EXCLUDED.prediction,                                memory_after,

                            confidence = EXCLUDED.confidence,                            )

                            features = EXCLUDED.features,                    compliance_status VARCHAR(50),

                            processing_time_ms = EXCLUDED.processing_time_ms                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

                        """,                );

                        result["call_id"],

                        result["prediction"],                CREATE INDEX IF NOT EXISTS idx_audit_trail_call_id

                        result["confidence"],                    ON audit_trail(call_id);

                        result.get("features"),                CREATE INDEX IF NOT EXISTS idx_audit_trail_event_type

                        result.get("processing_time_ms"),                    ON audit_trail(event_type);

                    )                CREATE INDEX IF NOT EXISTS idx_audit_trail_created_at

                    ON audit_trail(created_at);

        except Exception as exc:                """

            self.logger.error("Error storing analysis result: %s", exc)            )

            raise

            # Model performance table

    async def get_analysis_result(self, call_id: str) -> Optional[Dict[str, Any]]:            await conn.execute(

        """Retrieve analysis result from database."""                """

        if not self.pool:                CREATE TABLE IF NOT EXISTS model_performance (

            raise RuntimeError("Database pool is not initialized")                    id SERIAL PRIMARY KEY,

                    model_version VARCHAR(50) NOT NULL,

        try:                    prediction_count INTEGER DEFAULT 0,

            async with self.pool.acquire() as conn:                    accuracy DECIMAL(5,4),

                row = await conn.fetchrow(                    drift_score DECIMAL(5,4),

                    """                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

                    SELECT * FROM analysis_results WHERE call_id = $1                );

                    """,

                    call_id,                CREATE INDEX IF NOT EXISTS idx_model_performance_version

                )                    ON model_performance(model_version);

                CREATE INDEX IF NOT EXISTS idx_model_performance_created_at

                if row:                    ON model_performance(created_at);

                    features = row["features"]                """

                    if isinstance(features, str):            )

                        try:

                            features = json.loads(features)    async def store_analysis_result(self, result: Dict[str, Any]):

                        except json.JSONDecodeError:        """Store analysis result in database."""

                            self.logger.debug(        try:

                                "Failed to decode features JSON for call %s",            async with self.pool.acquire() as conn:

                                row["call_id"],                async with conn.transaction():

                            )                    await conn.execute(

                        """

                    processing_time = row["processing_time_ms"]                        INSERT INTO analysis_results (

                    if processing_time is not None:                            call_id,

                        processing_time = float(processing_time)                            prediction,

                            confidence,

                    try:                            features,

                        confidence = float(row["confidence"])                            processing_time_ms

                    except (TypeError, ValueError) as exc:                        )

                        self.logger.error(                        VALUES ($1, $2, $3, $4, $5)

                            "Error retrieving analysis result for %s: %s",                        ON CONFLICT (call_id) DO UPDATE SET

                            call_id,                            prediction = EXCLUDED.prediction,

                            exc,                            confidence = EXCLUDED.confidence,

                        )                            features = EXCLUDED.features,

                        return None                            processing_time_ms = EXCLUDED.processing_time_ms

                        """,

                    return {                        result['call_id'],

                        "id": row["id"],                        result['prediction'],

                        "call_id": row["call_id"],                        result['confidence'],

                        "prediction": row["prediction"],                        result.get('features'),

                        "confidence": confidence,                        result.get('processing_time_ms'),

                        "features": features,                    )

                        "processing_time_ms": processing_time,

                        "created_at": row["created_at"].isoformat(),        except Exception as e:

                    }            self.logger.error(f"Error storing analysis result: {e}")

            raise

        except Exception as exc:

            self.logger.error("Error retrieving analysis result: %s", exc)    async def get_analysis_result(

        self,

        return None        call_id: str,

    ) -> Optional[Dict[str, Any]]:

    async def log_audit_event(        """Retrieve analysis result from database."""

        self,        try:

        event_type: str,            async with self.pool.acquire() as conn:

        call_id: Optional[str] = None,                row = await conn.fetchrow("""

        session_id: Optional[str] = None,                    SELECT * FROM analysis_results WHERE call_id = $1

        metadata: Optional[Dict[str, Any]] = None,                """, call_id)

    ) -> None:

        """Log audit event to database."""                if row:

        if not self.pool:                    features = row['features']

            raise RuntimeError("Database pool is not initialized")                    if isinstance(features, str):

                        try:

        try:                            features = json.loads(features)

            async with self.pool.acquire() as conn:                        except json.JSONDecodeError:

                await conn.execute(                            self.logger.debug(

                    """                                "Failed to decode features JSON for call %s",

                    INSERT INTO audit_trail (                                row['call_id'],

                        event_type,                            )

                        call_id,

                        session_id,                    processing_time = row['processing_time_ms']

                        metadata,                    if processing_time is not None:

                        compliance_status                        processing_time = float(processing_time)

                    )

                    VALUES ($1, $2, $3, $4, $5)                    return {

                    """,                        'id': row['id'],

                    event_type,                        'call_id': row['call_id'],

                    call_id,                        'prediction': row['prediction'],

                    session_id,                        'confidence': float(row['confidence']),

                    metadata or {},                        'features': features,

                    "COMPLIANT",                        'processing_time_ms': processing_time,

                )                        'created_at': row['created_at'].isoformat(),

                    }

        except Exception as exc:

            self.logger.error("Error logging audit event: %s", exc)        except Exception as e:

            raise            self.logger.error(f"Error retrieving analysis result: {e}")



    async def get_compliance_report(        return None

        self,

        start_date: str,    async def log_audit_event(

        end_date: str,        self,

    ) -> Dict[str, Any]:        event_type: str,

        """Generate compliance report for audit purposes."""        call_id: Optional[str] = None,

        if not self.pool:        session_id: Optional[str] = None,

            raise RuntimeError("Database pool is not initialized")        metadata: Optional[Dict] = None,

    ):

        try:        """Log audit event to database."""

            async with self.pool.acquire() as conn:        try:

                analysis_stats = await conn.fetchrow(            async with self.pool.acquire() as conn:

                    """                await conn.execute(

                    SELECT                    """

                        COUNT(*) AS total_analyses,                    INSERT INTO audit_trail (

                        COUNT(CASE WHEN prediction = 'AI' THEN 1 END) AS ai_predictions,                        event_type,

                        COUNT(CASE WHEN prediction = 'HUMAN' THEN 1 END) AS human_predictions,                        call_id,

                        AVG(confidence) AS avg_confidence,                        session_id,

                        AVG(processing_time_ms) AS avg_processing_time                        metadata,

                    FROM analysis_results                        compliance_status

                    WHERE created_at BETWEEN $1 AND $2                    )

                    """,                    VALUES ($1, $2, $3, $4, $5)

                    start_date,                    """,

                    end_date,                    event_type,

                )                    call_id,

                    session_id,

                audit_stats = await conn.fetchrow(                    metadata or {},

                    """                    'COMPLIANT',

                    SELECT                )

                        COUNT(*) AS total_events,

                        COUNT(CASE WHEN compliance_status = 'COMPLIANT' THEN 1 END) AS compliant_events,        except Exception as e:

                        COUNT(CASE WHEN compliance_status = 'DEGRADED' THEN 1 END) AS degraded_events            self.logger.error(f"Error logging audit event: {e}")

                    FROM audit_trail            raise

                    WHERE created_at BETWEEN $1 AND $2

                    """,    async def get_compliance_report(

                    start_date,        self,

                    end_date,        start_date: str,

                )        end_date: str,

    ) -> Dict[str, Any]:

                avg_confidence = analysis_stats["avg_confidence"] or 0        """Generate compliance report for audit purposes."""

                avg_processing = analysis_stats["avg_processing_time"] or 0        try:

            async with self.pool.acquire() as conn:

                total_events = audit_stats["total_events"] or 0                # Get analysis statistics

                compliant_events = audit_stats["compliant_events"] or 0                analysis_stats = await conn.fetchrow(

                compliance_rate = 100.0                    """

                if total_events > 0:                    SELECT

                    compliance_rate = (compliant_events / total_events) * 100                        COUNT(*) AS total_analyses,

                        COUNT(

                analysis_summary = {                            CASE WHEN prediction = 'AI' THEN 1 END

                    "total": analysis_stats["total_analyses"],                        ) AS ai_predictions,

                    "ai_predictions": analysis_stats["ai_predictions"],                        COUNT(

                    "human_predictions": analysis_stats["human_predictions"],                            CASE WHEN prediction = 'HUMAN' THEN 1 END

                    "average_confidence": float(avg_confidence),                        ) AS human_predictions,

                    "average_processing_time_ms": float(avg_processing),                        AVG(confidence) AS avg_confidence,

                }                        AVG(processing_time_ms) AS avg_processing_time

                    FROM analysis_results

                audit_summary = {                    WHERE created_at BETWEEN $1 AND $2

                    "total_events": total_events,                    """,

                    "compliant_events": compliant_events,                    start_date,

                    "degraded_events": audit_stats["degraded_events"] or 0,                    end_date,

                    "compliance_rate": compliance_rate,                )

                }

                # Get audit statistics

                return {                audit_stats = await conn.fetchrow(

                    "period": {"start": start_date, "end": end_date},                    """

                    "analysis": analysis_summary,                    SELECT

                    "audit": audit_summary,                        COUNT(*) AS total_events,

                    "generated_at": datetime.utcnow().isoformat(),                        COUNT(

                }                            CASE WHEN compliance_status = 'COMPLIANT'

                            THEN 1 END

        except Exception as exc:                        ) AS compliant_events,

            self.logger.error("Error generating compliance report: %s", exc)                        COUNT(

            return {"error": str(exc)}                            CASE WHEN compliance_status = 'DEGRADED'

                            THEN 1 END

    async def get_system_metrics(self) -> Dict[str, Any]:                        ) AS degraded_events

        """Get system performance metrics."""                    FROM audit_trail

        if not self.pool:                    WHERE created_at BETWEEN $1 AND $2

            raise RuntimeError("Database pool is not initialized")                    """,

                    start_date,

        try:                    end_date,

            async with self.pool.acquire() as conn:                )

                metrics = await conn.fetchrow(

                    """                avg_confidence = analysis_stats['avg_confidence'] or 0

                    SELECT                avg_processing = analysis_stats['avg_processing_time'] or 0

                        COUNT(*) AS total_analyses_24h,

                        AVG(processing_time_ms) AS avg_latency_24h,                total_events = audit_stats['total_events'] or 0

                        MIN(created_at) AS first_analysis,                compliant_events = audit_stats['compliant_events'] or 0

                        MAX(created_at) AS last_analysis                compliance_rate = 100

                    FROM analysis_results                if total_events > 0:

                    WHERE created_at > NOW() - INTERVAL '24 hours'                    compliance_rate = (compliant_events / total_events) * 100

                    """

                )                analysis_summary = {

                    'total': analysis_stats['total_analyses'],

                avg_latency = metrics["avg_latency_24h"] or 0                    'ai_predictions': analysis_stats['ai_predictions'],

                    'human_predictions': analysis_stats['human_predictions'],

                return {                    'average_confidence': float(avg_confidence),

                    "total_analyses_24h": metrics["total_analyses_24h"],                    'average_processing_time_ms': float(avg_processing),

                    "average_latency_24h_ms": float(avg_latency),                }

                    "uptime_hours": 24,

                    "database_status": "healthy",                audit_summary = {

                }                    'total_events': total_events,

                    'compliant_events': compliant_events,

        except Exception as exc:                    'degraded_events': audit_stats['degraded_events'] or 0,

            self.logger.error("Error getting system metrics: %s", exc)                    'compliance_rate': compliance_rate,

            return {"error": str(exc)}                }



    def _sample_memory_usage(self) -> Optional[int]:                return {

        """Return current traced memory if tracemalloc is active."""                    'period': {'start': start_date, 'end': end_date},

        if tracemalloc.is_tracing():                    'analysis': analysis_summary,

            current, _ = tracemalloc.get_traced_memory()                    'audit': audit_summary,

            return current                    'generated_at': datetime.utcnow().isoformat(),

        return None                }



    def _estimate_pool_connections(self, pool: Any) -> Optional[int]:        except Exception as e:

        """Best-effort estimation of active connections for logging."""            self.logger.error(f"Error generating compliance report: {e}")

        for attr in ("connection_count", "total_connections"):            return {'error': str(e)}

            value = getattr(pool, attr, None)

            if isinstance(value, int):    async def get_system_metrics(self) -> Dict[str, Any]:

                return value        """Get system performance metrics."""

        holders = getattr(pool, "_holders", None)        try:

        if isinstance(holders, list):            async with self.pool.acquire() as conn:

            return len(holders)                # Get recent performance data

        return None                metrics = await conn.fetchrow("""

                    SELECT

    def _log_pool_teardown_metrics(                        COUNT(*) as total_analyses_24h,

        self,                        AVG(processing_time_ms) as avg_latency_24h,

        reason: str,                        MIN(created_at) as first_analysis,

        duration: float,                        MAX(created_at) as last_analysis

        connections: Optional[int],                    FROM analysis_results

        memory_before: Optional[int],                    WHERE created_at > NOW() - INTERVAL '24 hours'

        memory_after: Optional[int],                """)

    ) -> None:

        """Emit metrics about pool teardown for observability."""                avg_latency = metrics['avg_latency_24h'] or 0

        self.logger.info(

            (                return {

                "PostgreSQL pool teardown (%s): duration=%.4fs connections=%s "                    'total_analyses_24h': metrics['total_analyses_24h'],

                "memory_before=%s memory_after=%s"                    'average_latency_24h_ms': float(avg_latency),

            ),                    'uptime_hours': 24,  # Would calculate actual uptime

            reason,                    'database_status': 'healthy'

            duration,                }

            connections if connections is not None else "unknown",

            memory_before if memory_before is not None else "n/a",        except Exception as e:

            memory_after if memory_after is not None else "n/a",            self.logger.error(f"Error getting system metrics: {e}")

        )            return {'error': str(e)}


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
