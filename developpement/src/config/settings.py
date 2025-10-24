"""
Settings - Application Configuration
===================================

Centralized configuration management for V.O.T. Guardian.

Features:
- Environment-based configuration
- Validation and type checking
- Hot reloading support
- Secure defaults

Author: Jean-Sébastien Beaulieu
"""

import os
from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Application settings with validation."""

    # API Settings
    api_host: str = field(default_factory=lambda: os.getenv('API_HOST', '0.0.0.0'))
    api_port: int = field(default_factory=lambda: int(os.getenv('API_PORT', '8080')))
    api_secret_key: str = field(default_factory=lambda: os.getenv('API_SECRET_KEY', 'dev-secret-key'))

    # Database Settings
    postgresql_url: str = field(default_factory=lambda: os.getenv('POSTGRESQL_URL', 'postgresql://localhost:5432/vot_guardian'))
    rethinkdb_host: str = field(default_factory=lambda: os.getenv('RETHINKDB_HOST', 'localhost'))
    rethinkdb_port: int = field(default_factory=lambda: int(os.getenv('RETHINKDB_PORT', '28015')))
    mindsdb_url: str = field(default_factory=lambda: os.getenv('MINDSDB_URL', 'http://localhost:47334'))

    # E2B Settings
    e2b_api_key: str = field(default_factory=lambda: os.getenv('E2B_API_KEY', ''))
    e2b_pool_min_size: int = field(default_factory=lambda: int(os.getenv('E2B_POOL_MIN_SIZE', '5')))
    e2b_pool_max_size: int = field(default_factory=lambda: int(os.getenv('E2B_POOL_MAX_SIZE', '50')))

    # Datadog Settings
    datadog_api_key: str = field(default_factory=lambda: os.getenv('DD_API_KEY', ''))
    datadog_service: str = field(default_factory=lambda: os.getenv('DD_SERVICE', 'vot-guardian'))
    datadog_env: str = field(default_factory=lambda: os.getenv('DD_ENV', 'development'))

    # ML Settings
    ml_model_path: str = field(default_factory=lambda: os.getenv('ML_MODEL_PATH', '/models/vot-cnn-lstm-v2.1.pth'))
    ml_confidence_threshold: float = field(default_factory=lambda: float(os.getenv('ML_CONFIDENCE_THRESHOLD', '0.5')))

    # Security Settings
    tenebris_max_time_ms: int = field(default_factory=lambda: int(os.getenv('TENEBRIS_MAX_TIME_MS', '100')))
    encryption_enabled: bool = field(default_factory=lambda: os.getenv('ENCRYPTION_ENABLED', 'true').lower() == 'true')

    # Performance Settings
    max_audio_file_size: int = field(default_factory=lambda: int(os.getenv('MAX_AUDIO_FILE_SIZE', '10485760')))
    audio_sample_rate: int = field(default_factory=lambda: int(os.getenv('AUDIO_SAMPLE_RATE', '16000')))
    processing_timeout: int = field(default_factory=lambda: int(os.getenv('PROCESSING_TIMEOUT', '30')))

    # Logging Settings
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    log_format: str = field(default_factory=lambda: os.getenv('LOG_FORMAT', 'json'))

    def __post_init__(self):
        """Validate settings after initialization."""
        self._validate_settings()

    def _validate_settings(self):
        """Validate that all settings are reasonable."""
        # Validate API settings
        if not self.api_secret_key or self.api_secret_key == 'dev-secret-key':
            import warnings
            warnings.warn("Using default API secret key - not secure for production!")

        # Validate port ranges
        if not (1 <= self.api_port <= 65535):
            raise ValueError(f"Invalid API port: {self.api_port}")

        # Validate file size limits
        if self.max_audio_file_size <= 0:
            raise ValueError(f"Invalid max audio file size: {self.max_audio_file_size}")

        # Validate confidence threshold
        if not (0 <= self.ml_confidence_threshold <= 1):
            raise ValueError(f"Invalid confidence threshold: {self.ml_confidence_threshold}")

        # Validate Tenebris timing
        if self.tenebris_max_time_ms <= 0:
            raise ValueError(f"Invalid Tenebris max time: {self.tenebris_max_time_ms}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            'api_host': self.api_host,
            'api_port': self.api_port,
            'postgresql_url': self.postgresql_url,
            'rethinkdb_host': self.rethinkdb_host,
            'rethinkdb_port': self.rethinkdb_port,
            'mindsdb_url': self.mindsdb_url,
            'e2b_api_key_configured': bool(self.e2b_api_key),
            'datadog_api_key_configured': bool(self.datadog_api_key),
            'ml_model_path': self.ml_model_path,
            'ml_confidence_threshold': self.ml_confidence_threshold,
            'tenebris_max_time_ms': self.tenebris_max_time_ms,
            'encryption_enabled': self.encryption_enabled,
            'max_audio_file_size': self.max_audio_file_size,
            'audio_sample_rate': self.audio_sample_rate,
            'processing_timeout': self.processing_timeout,
            'log_level': self.log_level,
            'log_format': self.log_format
        }

    def is_production_ready(self) -> bool:
        """Check if settings are suitable for production."""
        checks = [
            bool(self.api_secret_key and self.api_secret_key != 'dev-secret-key'),
            bool(self.e2b_api_key),
            bool(self.datadog_api_key),
            self.encryption_enabled,
            self.log_level.upper() in ['WARNING', 'ERROR', 'CRITICAL'],
            self.tenebris_max_time_ms <= 100
        ]

        return all(checks)

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for clients."""
        return {
            'postgresql': {
                'url': self.postgresql_url,
                'min_connections': 5,
                'max_connections': 20
            },
            'rethinkdb': {
                'host': self.rethinkdb_host,
                'port': self.rethinkdb_port,
                'db': 'vot_guardian'
            },
            'mindsdb': {
                'url': self.mindsdb_url,
                'timeout': 30
            }
        }

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return {
            'datadog': {
                'api_key': self.datadog_api_key,
                'service': self.datadog_service,
                'env': self.datadog_env,
                'enabled': bool(self.datadog_api_key)
            },
            'metrics': {
                'enabled': os.getenv('METRICS_ENABLED', 'true').lower() == 'true',
                'port': int(os.getenv('METRICS_PORT', '9090'))
            }
        }

    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            'tenebris': {
                'max_execution_time_ms': self.tenebris_max_time_ms,
                'encryption_enabled': self.encryption_enabled,
                'audit_enabled': True
            },
            'ssl': {
                'enabled': os.getenv('SSL_ENABLED', 'false').lower() == 'true',
                'cert_path': os.getenv('SSL_CERT_PATH'),
                'key_path': os.getenv('SSL_KEY_PATH')
            }
        }


# Global settings instance
settings = Settings()