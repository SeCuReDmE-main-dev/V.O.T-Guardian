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

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import asyncpg


@dataclass
class DatabaseConfig:
    """Configuration for PostgreSQL database."""
    url: str
    min_connections: int = 5
    max_connections: int = 20
    command_timeout: int = 60
    server_settings: Dict[str, str] = None


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
        )

    async def connect(self):
        """Create database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.config.url,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout,
                server_settings=self.config.server_settings or {}
            )

            # Create tables if they don't exist
            await self._initialize_tables()

            self.logger.info("Connected to PostgreSQL database")

        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            self.logger.info("Disconnected from PostgreSQL database")

    async def _initialize_tables(self):
        """Create database tables if they don't exist."""
        async with self.pool.acquire() as conn:
            # Analysis results table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id SERIAL PRIMARY KEY,
                    call_id VARCHAR(255) NOT NULL,
                    prediction VARCHAR(50) NOT NULL,
                    confidence DECIMAL(5,4) NOT NULL,
                    features JSONB,
                    processing_time_ms DECIMAL(8,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(call_id)
                );

                CREATE INDEX IF NOT EXISTS idx_analysis_results_call_id
                    ON analysis_results(call_id);
                CREATE INDEX IF NOT EXISTS idx_analysis_results_created_at
                    ON analysis_results(created_at);
                CREATE INDEX IF NOT EXISTS idx_analysis_results_prediction
                    ON analysis_results(prediction);
                """
            )

            # Audit trail table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(100) NOT NULL,
                    call_id VARCHAR(255),
                    session_id VARCHAR(255),
                    metadata JSONB,
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

    async def get_analysis_result(self, call_id: str) -> Optional[Dict[str, Any]]:
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

                    return {
                        'id': row['id'],
                        'call_id': row['call_id'],
                        'prediction': row['prediction'],
                        'confidence': float(row['confidence']),
                        'features': features,
                        'processing_time_ms': float(row['processing_time_ms']) if row['processing_time_ms'] else None,
                        'created_at': row['created_at'].isoformat()
                    }

        except Exception as e:
            self.logger.error(f"Error retrieving analysis result: {e}")

        return None

    async def log_audit_event(self, event_type: str, call_id: Optional[str] = None,
                            session_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """Log audit event to database."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO audit_trail (event_type, call_id, session_id, metadata, compliance_status)
                    VALUES ($1, $2, $3, $4, $5)
                """, event_type, call_id, session_id, metadata or {}, 'COMPLIANT')

        except Exception as e:
            self.logger.error(f"Error logging audit event: {e}")
            raise

    async def get_compliance_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Generate compliance report for audit purposes."""
        try:
            async with self.pool.acquire() as conn:
                # Get analysis statistics
                analysis_stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_analyses,
                        COUNT(CASE WHEN prediction = 'AI' THEN 1 END) as ai_predictions,
                        COUNT(CASE WHEN prediction = 'HUMAN' THEN 1 END) as human_predictions,
                        AVG(confidence) as avg_confidence,
                        AVG(processing_time_ms) as avg_processing_time
                    FROM analysis_results
                    WHERE created_at BETWEEN $1 AND $2
                """, start_date, end_date)

                # Get audit statistics
                audit_stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_events,
                        COUNT(CASE WHEN compliance_status = 'COMPLIANT' THEN 1 END) as compliant_events,
                        COUNT(CASE WHEN compliance_status = 'DEGRADED' THEN 1 END) as degraded_events
                    FROM audit_trail
                    WHERE created_at BETWEEN $1 AND $2
                """, start_date, end_date)

                return {
                    'period': {'start': start_date, 'end': end_date},
                    'analysis': {
                        'total': analysis_stats['total_analyses'],
                        'ai_predictions': analysis_stats['ai_predictions'],
                        'human_predictions': analysis_stats['human_predictions'],
                        'average_confidence': float(analysis_stats['avg_confidence']) if analysis_stats['avg_confidence'] else 0,
                        'average_processing_time_ms': float(analysis_stats['avg_processing_time']) if analysis_stats['avg_processing_time'] else 0
                    },
                    'audit': {
                        'total_events': audit_stats['total_events'],
                        'compliant_events': audit_stats['compliant_events'],
                        'degraded_events': audit_stats['degraded_events'],
                        'compliance_rate': (audit_stats['compliant_events'] / audit_stats['total_events'] * 100) if audit_stats['total_events'] > 0 else 100
                    },
                    'generated_at': datetime.utcnow().isoformat()
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

                return {
                    'total_analyses_24h': metrics['total_analyses_24h'],
                    'average_latency_24h_ms': float(metrics['avg_latency_24h']) if metrics['avg_latency_24h'] else 0,
                    'uptime_hours': 24,  # Would calculate actual uptime
                    'database_status': 'healthy'
                }

        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {'error': str(e)}