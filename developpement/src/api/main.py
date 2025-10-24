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
import asyncio
# import time  # no longer used in the real endpoint step
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
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
    """
    Real analysis endpoint (Step 1: E2B pipeline validation)

    Accepts an audio file, starts an E2B sandbox, sends the file into the
    sandbox, executes a tiny Python snippet to confirm receipt, and returns a
    simple JSON.
    """
    try:
        if 'audio' not in request.files:
            raise BadRequest("No audio file provided")

        audio_file = request.files['audio']
        audio_bytes = audio_file.read()

        async def _sandbox_receive_file(data: bytes) -> str:
            try:
                async with e2b_manager.get_sandbox() as sandbox:
                    # Write file into sandbox FS
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: sandbox.files.write('input_audio.bin', data)
                    )

                    # Simple confirmation script
                    code = (
                        "with open('input_audio.bin','rb') as f:\n"
                        "    b = f.read()\n"
                        "print(f'Fichier reçu avec la taille {len(b)}')\n"
                    )

                    result = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: sandbox.run_code(code)
                    )

                    return (result.text or '').strip()
            except Exception as se:
                logger.error(f"Sandbox error: {se}")
                return f"Sandbox error: {se}"

        # Run the async sandbox interaction
        sandbox_message = asyncio.run(_sandbox_receive_file(audio_bytes))

        return jsonify({
            "status": "real_endpoint_hit",
            "sandbox_message": (
                sandbox_message or "Fichier reçu dans le sandbox"
            ),
        }), 200

    except BadRequest as br:
        return jsonify({
            'error': 'Bad request',
            'message': str(br)
        }), 400
    except Exception as e:
        logger.error(f"/analyze error: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
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
    app.run(
        host=os.getenv('API_HOST', '0.0.0.0'),
        port=int(os.getenv('API_PORT', 8080)),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )
