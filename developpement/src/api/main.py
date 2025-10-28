"""
V.O.T. Guardian API - Main Application
=====================================

Flask API for voice authentication and fraud detection.

Endpoints:
- POST /analyze : Analyze audio for AI-generated content
- GET /health : Health check endpoint
- GET /metrics : Prometheus metrics

Security: Protocole Tenebris implementation
Monitoring: Datadog integration
"""

import os
import json
import asyncio
import importlib
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict
from flask import Flask, request, jsonify
from flask_cors import CORS
try:
    # Load environment variables from a local .env if present
    from dotenv import load_dotenv, find_dotenv  # type: ignore
    _dotenv_path = find_dotenv()
    if _dotenv_path:
        load_dotenv(_dotenv_path)
    else:
        # Fallback: try project-specific path (developpement/.env)
        _here = os.path.dirname(os.path.abspath(__file__))
        _proj_env = os.path.normpath(os.path.join(_here, '..', '..', '.env'))
        if os.path.exists(_proj_env):
            load_dotenv(_proj_env)
except Exception:
    # python-dotenv not installed or other issue; continue without it
    pass
try:
    # Direct E2B SDK import for one-off sandboxes with internet access
    E2BSandbox = importlib.import_module('e2b_code_interpreter').Sandbox
except Exception:  # pragma: no cover
    E2BSandbox = None
try:
    # Generic E2B SDK that supports custom templates
    GenericE2BSandbox = importlib.import_module('e2b').Sandbox
except Exception:  # pragma: no cover
    GenericE2BSandbox = None
from werkzeug.exceptions import BadRequest

# Import core modules
from ..core.security.tenebris import TenebrisProtocol
from ..core.monitoring.datadog_client import DatadogClient
from ..core.e2b.sandbox_manager import E2BSandboxManager
from ..core.audio.processor import AudioProcessor
from ..core.ml.predictor import MLPredictor
from ..core.database.postgresql_client import PostgreSQLClient
from ..config.settings import Settings

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('API_SECRET_KEY', 'dev-secret-key')

# Enable CORS for frontend (Vite dev server on port 5173)
CORS(
    app,
    resources={r"*": {"origins": [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]}},
)

# Initialize core components
settings = Settings()
tenebris = TenebrisProtocol()
datadog = DatadogClient()
e2b_manager = E2BSandboxManager()
audio_processor = AudioProcessor()
ml_predictor = MLPredictor()
db_client = PostgreSQLClient()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _get_call_id() -> str:
    """Return a sanitized call identifier or generate one."""
    provided = request.form.get('call_id') or request.args.get('call_id')
    if provided:
        return str(provided)
    return f"call_{uuid.uuid4().hex}"


async def _process_analysis_request(
    call_id: str,
    audio_bytes: bytes,
) -> Dict[str, Any]:
    """Run the end-to-end analysis pipeline asynchronously."""
    pipeline_start = time.perf_counter()

    if not audio_processor.validate_audio_format(audio_bytes):
        raise BadRequest("Unsupported audio format or duration")

    async with tenebris.execute_protocol(call_id) as sandbox_id:
        features = audio_processor.process_audio_data(audio_bytes)
        prediction = await ml_predictor.predict(features)

        total_processing_time_ms = (
            time.perf_counter() - pipeline_start
        ) * 1000
        response_payload = _build_response_payload(
            call_id,
            prediction,
            features,
            sandbox_id,
            total_processing_time_ms,
        )

        await _persist_analysis_result(response_payload, features, sandbox_id)
        _record_metrics(response_payload, features, sandbox_id)

        return response_payload


async def _persist_analysis_result(
    response_payload: Dict[str, Any],
    features: Dict[str, float],
    sandbox_id: str,
) -> None:
    """Store analysis output and audit trail; failures are logged only."""
    try:
        await _ensure_db_connection()
    # Store features as JSON text to satisfy asyncpg's JSONB parameter handling.
    features_payload = json.dumps(features)
        await db_client.store_analysis_result({
            'call_id': response_payload['call_id'],
            'prediction': response_payload['prediction'],
            'confidence': response_payload['confidence'],
            'features': features_payload,
            'processing_time_ms': response_payload['processing_time_ms'],
        })

        metadata_payload = json.dumps({
            'prediction': response_payload['prediction'],
            'confidence': response_payload['confidence'],
            'model_version': response_payload.get('model_version'),
            'features': features,
        })

        await db_client.log_audit_event(
            event_type='ANALYSIS_COMPLETED',
            call_id=response_payload['call_id'],
            session_id=sandbox_id,
            metadata=metadata_payload,
        )
    # pragma: no cover - persistence issues shouldn't block response
    except Exception as persist_error:
        logger.warning(
            "Failed to persist analysis or audit trail for %s: %s",
            response_payload['call_id'],
            persist_error,
        )


async def _ensure_db_connection() -> None:
    """Ensure the PostgreSQL connection pool is available."""
    if db_client.pool is None:
        await db_client.connect()


def _record_metrics(
    response_payload: Dict[str, Any],
    features: Dict[str, float],
    sandbox_id: str,
) -> None:
    """Emit monitoring metrics; best-effort only."""
    try:
        datadog.record_analysis_metrics(
            call_id=response_payload['call_id'],
            prediction=response_payload['prediction'],
            confidence=response_payload['confidence'],
            latency_ms=response_payload['processing_time_ms'],
        )

        snr_db = features.get('snr_db', 0.0)
        thd_percent = features.get('thd_percent', 0.0)
        datadog.record_audio_quality_metrics(
            call_id=response_payload['call_id'],
            snr_db=snr_db,
            thd_percent=thd_percent,
            clipping_ratio=features.get('zero_crossing_rate', 0.0),
        )

        datadog.record_tenebris_metrics(
            call_id=response_payload['call_id'],
            destruction_time_ms=response_payload.get(
                'tenebris_destruction_time_ms',
                0.0,
            ),
            compliance_status='COMPLIANT',
        )
    # pragma: no cover - metrics failures are non-blocking
    except Exception as metrics_error:
        logger.debug(
            "Metrics emission failed for %s: %s",
            sandbox_id,
            metrics_error,
        )


def _build_response_payload(
    call_id: str,
    prediction: Dict[str, Any],
    features: Dict[str, float],
    sandbox_id: str,
    total_processing_time_ms: float,
) -> Dict[str, Any]:
    """Shape the JSON returned to the frontend."""
    return {
        'call_id': call_id,
        'prediction': prediction.get('prediction', 'UNKNOWN'),
        'confidence': prediction.get('confidence', 0.0),
        'processing_time_ms': round(total_processing_time_ms, 2),
        'model_processing_time_ms': round(
            prediction.get('processing_time_ms', 0.0),
            2,
        ),
        'status': 'success',
        'features': features,
        'model_version': prediction.get('model_version'),
        'probabilities': prediction.get('probabilities'),
        'tenebris_session': sandbox_id,
        'tenebris_destruction_time_ms': prediction.get(
            'tenebris_destruction_time_ms',
            0.0,
        ),
    }


@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information."""
    return jsonify({
        'service': 'V.O.T. Guardian API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'analyze': 'POST /analyze',
            'analyze_mock': 'POST /api/v1/analyze',
            'metrics': '/metrics'
        },
        'documentation': 'Send POST request to /analyze with audio file'
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for load balancer."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'service': 'vot-guardian-api'
    })


@app.route('/analyze', methods=['POST'])
def analyze_audio():
    """Main analysis endpoint connecting the full processing pipeline."""
    try:
        if 'audio' not in request.files:
            raise BadRequest("No audio file provided")

        audio_file = request.files['audio']
        audio_bytes = audio_file.read()
        call_id = _get_call_id()

        if not audio_bytes:
            raise BadRequest("Empty audio payload")

        if len(audio_bytes) > settings.max_audio_file_size:
            raise BadRequest("Audio file exceeds maximum size limit")

        result = asyncio.run(_process_analysis_request(call_id, audio_bytes))
        return jsonify(result), 200

    except BadRequest as br:
        return jsonify({
            'error': 'Bad request',
            'message': str(br)
        }), 400
    except RuntimeError as runtime_error:
        # asyncio.run cannot be nested; surface as server error
        logger.error(f"Runtime error in /analyze: {runtime_error}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Analysis service unavailable'
        }), 500
    except Exception as exc:  # pragma: no cover
        logger.error(f"/analyze error: {exc}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': 'Unexpected failure during analysis'
        }), 500


@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint."""
    # This would integrate with Prometheus client
    # For now, return basic metrics
    return jsonify({
        'total_requests': 0,
        'successful_analyses': 0,
        'failed_analyses': 0,
        'average_latency_ms': 0
    })


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({
        'error': 'File too large',
        'message': 'Audio file exceeds maximum size limit'
    }), 413


@app.errorhandler(415)
def unsupported_media(e):
    """Handle unsupported media type."""
    return jsonify({
        'error': 'Unsupported media type',
        'message': 'Audio file format not supported'
    }), 415


@app.route('/api/v1/analyze', methods=['POST'])
def analyze_mock():
    """Mock analysis endpoint for the simulated pipeline step.

    Returns a fixed JSON payload to unblock frontend integration.
    """
    return jsonify({
        "is_ai_voice": True,
        "score": 0.98,
        "message": "Analysis complete (simulated)",
    }), 200


if __name__ == '__main__':
    # Reuse validated settings for host/port
    app.run(
        host=settings.api_host,
        port=settings.api_port,
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )
