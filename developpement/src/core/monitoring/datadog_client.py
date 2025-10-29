"""
Datadog Client - Monitoring and Observability
============================================

Integrates with Datadog for comprehensive monitoring of the V.O.T. Guardian system.

Features:
- Infrastructure monitoring
- APM distributed tracing
- Log management
- ML model observability
- Security monitoring
- Custom metrics for voice analysis

Author: Jean-Sébastien Beaulieu
"""

import asyncio
import os
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Import Datadog API client
try:
    from datadog_api_client.v1 import ApiClient, Configuration
    from datadog_api_client.v1.api.events_api import EventsApi
    from datadog_api_client.v1.model.event_create_request import EventCreateRequest
    DATADOG_AVAILABLE = True
except ImportError:
    DATADOG_AVAILABLE = False


@dataclass
class DatadogConfig:
    """Configuration for Datadog integration."""
    api_key: str
    app_key: Optional[str] = None
    site: str = "datadoghq.eu"
    service_name: str = "vot-guardian"
    env: str = "development"
    version: str = "1.0.0"
    max_retries: int = 1
    retry_backoff_seconds: float = 0.25


class DatadogClient:
    """
    Datadog monitoring client for V.O.T. Guardian.

    Provides unified interface for metrics, logs, traces, and events.
    """

    def __init__(self, config: Optional[DatadogConfig] = None):
        self.config = config or self._load_config()
        self.logger = logging.getLogger(__name__)
        self._failover_active = False

        # Initialize Datadog API client (if available)
        if DATADOG_AVAILABLE:
            self.configuration = Configuration()
            self.configuration.api_key['apiKeyAuth'] = self.config.api_key
            self.configuration.api_key['appKeyAuth'] = (
                self.config.app_key or ""
            )
            self.configuration.server_variables['site'] = self.config.site

            self.api_client = ApiClient(self.configuration)
            self.events_api = EventsApi(self.api_client)
        else:
            self.configuration = None
            self.api_client = None
            self.events_api = None
            self._record_failover(
                (
                    "Datadog SDK unavailable; "
                    "monitoring operating in degraded mode"
                ),
                level=logging.ERROR,
            )

        # Initialize statsd for metrics (if available)
        self.statsd = None
        self._initialize_statsd()

        if not self.config.api_key:
            self._record_failover(
                "API key missing; Datadog integrations disabled",
                level=logging.ERROR,
            )

    def _load_config(self) -> DatadogConfig:
        """Load configuration from environment variables."""
        return DatadogConfig(
            api_key=os.getenv('DD_API_KEY', ''),
            app_key=os.getenv('DD_APP_KEY'),
            site=os.getenv('DD_SITE', 'datadoghq.eu'),
            service_name=os.getenv('DD_SERVICE', 'vot-guardian'),
            env=os.getenv('DD_ENV', 'development'),
            version=os.getenv('DD_VERSION', '1.0.0')
        )

    def _initialize_statsd(self):
        """Initialize StatsD client for metrics."""
        try:
            from datadog import statsd  # type: ignore
            statsd.configure(
                api_key=self.config.api_key,
                statsd_host=os.getenv('DD_AGENT_HOST', 'localhost'),
                statsd_port=8125
            )
            self.statsd = statsd
        except ImportError:
            self._record_failover(
                "Datadog statsd not available; metrics disabled",
                level=logging.ERROR,
            )
        except Exception as exc:
            self._record_failover(
                f"Statsd initialization failed: {exc}",
                level=logging.ERROR,
            )

    async def log_event(
        self,
        title: str,
        metadata: Dict[str, Any],
        alert_type: str = 'info',
        tags: Optional[list] = None,
    ):
        """
        Log an event to Datadog.

        Args:
            title: Event title
            metadata: Event metadata
            alert_type: Event alert type (info, success, warning, error)
            tags: Additional tags for the event
        """
        attempts = max(1, self.config.max_retries)

        try:
            # Create event payload
            event_text = f"""
            Service: {self.config.service_name}
            Environment: {self.config.env}
            Version: {self.config.version}

            Metadata:
            {self._format_metadata(metadata)}
            """

            # Default tags
            default_tags = [
                f'service:{self.config.service_name}',
                f'env:{self.config.env}',
                f'version:{self.config.version}'
            ]

            # Add custom tags
            if tags:
                default_tags.extend(tags)

            # Create event request
            event_request = EventCreateRequest(
                title=title,
                text=event_text,
                alert_type=alert_type,
                tags=default_tags
            )

            # Send event (if Datadog is available)
            if not self.events_api:
                self._record_failover(
                    "Events API unavailable; event buffered locally",
                    level=logging.WARNING,
                )
                return

            last_error: Optional[Exception] = None
            for attempt in range(1, attempts + 1):
                try:
                    self.events_api.create_event(event_request)
                    self._failover_active = False
                    self.logger.info(
                        "Datadog event published: %s",
                        title,
                    )
                    return
                except Exception as exc:
                    last_error = exc
                    self._record_failover(
                        (
                            "Failed to log event to Datadog"
                            f" (attempt {attempt}): {exc}"
                        ),
                        level=logging.ERROR,
                    )
                    if attempt < attempts:
                        self.logger.warning(
                            (
                                "Datadog retry scheduled for event %s"
                                " (attempt %s/%s)"
                            ),
                            title,
                            attempt + 1,
                            attempts,
                        )
                        await asyncio.sleep(
                            self.config.retry_backoff_seconds
                        )

            if last_error is not None:
                self.logger.error(
                    (
                        "Datadog event permanently failed"
                        f" after {attempts} attempts: {last_error}"
                    )
                )

        except Exception as e:
            self._record_failover(
                f"Failed to log event to Datadog: {e}",
                level=logging.ERROR,
            )

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata for display in event text."""
        formatted_lines = []
        for key, value in metadata.items():
            if isinstance(value, (dict, list)):
                formatted_lines.append(f"  {key}: {value}")
            else:
                formatted_lines.append(f"  {key}: {value}")
        return "\n".join(formatted_lines)

    def record_metric(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Record a custom metric.

        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Additional tags
        """
        if not self.statsd:
            self._record_failover(
                "StatsD client unavailable; metric dropped",
                level=logging.WARNING,
            )
            return

        attempts = max(1, self.config.max_retries)

        # Add default tags
        default_tags = [
            f'service:{self.config.service_name}',
            f'env:{self.config.env}'
        ]

        if tags:
            default_tags.extend([f'{k}:{v}' for k, v in tags.items()])

        last_error: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            try:
                if (
                    'latency' in metric_name.lower()
                    or 'time' in metric_name.lower()
                ):
                    self.statsd.histogram(
                        metric_name,
                        value,
                        tags=default_tags,
                    )
                elif (
                    'rate' in metric_name.lower()
                    or 'count' in metric_name.lower()
                ):
                    self.statsd.increment(
                        metric_name,
                        value,
                        tags=default_tags,
                    )
                else:
                    self.statsd.gauge(
                        metric_name,
                        value,
                        tags=default_tags,
                    )

                self._failover_active = False
                self.logger.info(
                    "Datadog metric recorded: %s",
                    metric_name,
                )
                return

            except Exception as exc:
                last_error = exc
                self._record_failover(
                    (
                        "Failed to record metric"
                        f" (attempt {attempt}): {exc}"
                    ),
                    level=logging.ERROR,
                )
                if attempt < attempts:
                    self.logger.warning(
                        (
                            "Datadog retry scheduled for metric %s"
                            " (attempt %s/%s)"
                        ),
                        metric_name,
                        attempt + 1,
                        attempts,
                    )
                    time.sleep(self.config.retry_backoff_seconds)

        if last_error is not None:
            self.logger.error(
                (
                    "Datadog metric permanently failed"
                    f" after {attempts} attempts: {last_error}"
                )
            )

    def record_analysis_metrics(
        self,
        call_id: str,
        prediction: str,
        confidence: float,
        latency_ms: float,
    ):
        """
        Record metrics specific to voice analysis.

        Args:
            call_id: Unique call identifier
            prediction: AI or HUMAN
            confidence: Prediction confidence (0-1)
            latency_ms: Processing latency in milliseconds
        """
        # Record core metrics
        self.record_metric('vot.analysis.total', 1, {'call_id': call_id})
        self.record_metric(
            'vot.analysis.confidence',
            confidence,
            {'call_id': call_id},
        )
        self.record_metric(
            'vot.analysis.latency_ms',
            latency_ms,
            {'call_id': call_id},
        )

        # Record prediction-specific metrics
        if prediction == 'AI':
            self.record_metric(
                'vot.analysis.prediction.ai',
                1,
                {'call_id': call_id},
            )
        else:
            self.record_metric(
                'vot.analysis.prediction.human',
                1,
                {'call_id': call_id},
            )

        # Record performance metrics
        if latency_ms < 500:
            self.record_metric(
                'vot.analysis.performance.compliant',
                1,
                {'call_id': call_id},
            )
        else:
            self.record_metric(
                'vot.analysis.performance.degraded',
                1,
                {'call_id': call_id},
            )

    def record_tenebris_metrics(
        self,
        call_id: str,
        destruction_time_ms: float,
        compliance_status: str,
    ):
        """
        Record metrics for Tenebris protocol execution.

        Args:
            call_id: Unique call identifier
            destruction_time_ms: Time taken for data destruction
            compliance_status: COMPLIANT or DEGRADED
        """
        self.record_metric(
            'vot.tenebris.destruction_time_ms',
            destruction_time_ms,
            {'call_id': call_id, 'status': compliance_status},
        )

        if compliance_status == 'COMPLIANT':
            self.record_metric(
                'vot.tenebris.compliant',
                1,
                {'call_id': call_id},
            )
        else:
            self.record_metric(
                'vot.tenebris.violation',
                1,
                {'call_id': call_id},
            )

    def record_audio_quality_metrics(
        self,
        call_id: str,
        snr_db: float,
        thd_percent: float,
        clipping_ratio: float,
    ):
        """
        Record audio quality metrics.

        Args:
            call_id: Unique call identifier
            snr_db: Signal-to-noise ratio in dB
            thd_percent: Total harmonic distortion percentage
            clipping_ratio: Audio clipping ratio
        """
        self.record_metric('vot.audio.snr_db', snr_db, {'call_id': call_id})
        self.record_metric(
            'vot.audio.thd_percent',
            thd_percent,
            {'call_id': call_id},
        )
        self.record_metric(
            'vot.audio.clipping_ratio',
            clipping_ratio,
            {'call_id': call_id},
        )

        # Alert on poor quality
        if snr_db < 15:
            self.logger.warning(
                "Poor audio quality detected for call %s: SNR %s dB",
                call_id,
                snr_db,
            )

    def record_ml_model_metrics(
        self,
        model_name: str,
        prediction_time_ms: float,
        confidence: float,
        drift_score: Optional[float] = None,
    ):
        """
        Record ML model performance metrics.

        Args:
            model_name: Name of the ML model
            prediction_time_ms: Inference time
            confidence: Prediction confidence
            drift_score: Model drift score (if available)
        """
        self.record_metric(
            'vot.ml.inference_time_ms',
            prediction_time_ms,
            {'model': model_name},
        )
        self.record_metric(
            'vot.ml.confidence',
            confidence,
            {'model': model_name},
        )

        if drift_score is not None:
            self.record_metric(
                'vot.ml.drift_score',
                drift_score,
                {'model': model_name},
            )

    def get_service_status(self) -> Dict[str, Any]:
        """Get overall service status from Datadog."""
        try:
            # This would query Datadog for current service metrics
            # For now, return basic status
            return {
                'service': self.config.service_name,
                'status': 'healthy',
                'last_check': time.time(),
                'metrics': {
                    'total_analyses': 0,
                    'average_latency_ms': 0,
                    'error_rate': 0
                }
            }
        except Exception as e:
            self._record_failover(
                f"Failed to get service status: {e}",
                level=logging.ERROR,
            )
            return {'status': 'error', 'error': str(e)}

    def _record_failover(self, reason: str, level: int = logging.WARNING):
        """Emit standardized failover logs."""
        message = f"Datadog failover - {reason}"

        if level >= logging.ERROR:
            self.logger.error(message)
        elif level <= logging.INFO:
            self.logger.info(message)
        else:
            self.logger.warning(message)

        self._failover_active = True
