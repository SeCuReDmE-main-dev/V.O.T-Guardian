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
    from e2b_code_interpreter import Sandbox as E2BSandbox
except Exception:  # pragma: no cover
    E2BSandbox = None
try:
    # Generic E2B SDK that supports custom templates
    from e2b import Sandbox as GenericE2BSandbox  # type: ignore
except Exception:  # pragma: no cover
    GenericE2BSandbox = None
from werkzeug.exceptions import BadRequest

# Import core modules
from ..core.security.tenebris import TenebrisProtocol
from ..core.monitoring.datadog_client import DatadogClient
from ..core.e2b.sandbox_manager import (
    E2BSandboxManager,
    run_python_code_in_sandbox,
)
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

        async def _sandbox_mindsdb_probe(data: bytes) -> dict:
            """
            Create a fresh sandbox with internet,
            pip install deps, run probe script, return outputs.
            """
            if E2BSandbox is None and GenericE2BSandbox is None:
                return {
                    "stdout": "E2B SDK not available",
                    "install_stdout": "",
                    "error": "E2B SDK missing",
                }

            # Allow internet and extend timeout to handle pip installs
            sandbox = None
            try:
                use_generic = (
                    bool(getattr(e2b_manager.config, 'template_id', None))
                    and GenericE2BSandbox is not None
                )

                if use_generic:
                    tmpl = (
                        e2b_manager.config.template_id
                        or 'vot-guardian-cpu-mid'
                    )
                    create_kwargs = {
                        'template': tmpl,
                        'allow_internet_access': True,
                    }
                    if e2b_manager.config.api_key:
                        create_kwargs['api_key'] = (
                            e2b_manager.config.api_key
                        )
                    sandbox = GenericE2BSandbox.create(**create_kwargs)
                else:
                    if E2BSandbox is None:
                        raise RuntimeError(
                            "Code Interpreter SDK not available"
                        )
                    create_kwargs = {
                        'allow_internet_access': True,
                        'timeout': max(
                            300,
                            e2b_manager.config.sandbox_timeout,
                        ),
                    }
                    if e2b_manager.config.api_key:
                        create_kwargs['api_key'] = (
                            e2b_manager.config.api_key
                        )
                    sandbox = E2BSandbox.create(**create_kwargs)

                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    lambda: sandbox.files.write('input_audio.bin', data),
                )

                def format_run_output(run_result: dict) -> str:
                    if not run_result:
                        return ''
                    if run_result.get('error'):
                        return f"error: {run_result['error']}"
                    text = (run_result.get('stdout') or '').strip()
                    if not text and run_result.get('stderr'):
                        text = str(run_result['stderr']).strip()
                    exit_code = run_result.get('exit_code')
                    if exit_code not in (0, None):
                        suffix = f"exit_code={exit_code}"
                        text = f"{text}\n{suffix}" if text else suffix
                    return text

                if use_generic:
                    install_result = {
                        'stdout': 'skipped (using E2B template)',
                        'stderr': '',
                        'exit_code': None,
                        'error': None,
                    }
                else:
                    install_code = (
                        "import subprocess, sys\n"
                        "pkgs = ['mindsdb', 'librosa', 'torch']\n"
                        "print('Installing packages:', pkgs)\n"
                        "cmd = [sys.executable, '-m', 'pip', 'install']"
                        " + pkgs\n"
                        "proc = subprocess.run(\n"
                        "    cmd, capture_output=True, text=True\n"
                        ")\n"
                        "print('pip returncode:', proc.returncode)\n"
                        "print('--- pip stdout ---')\n"
                        "print(proc.stdout)\n"
                        "print('--- pip stderr ---')\n"
                        "print(proc.stderr)\n"
                    )
                    install_result = await loop.run_in_executor(
                        None,
                        lambda: run_python_code_in_sandbox(
                            sandbox,
                            install_code,
                        ),
                    )

                install_out = format_run_output(install_result)

                probe_code = (
                    "print('Importing libraries...')\n"
                    "import importlib\n"
                    "modules = ['librosa', 'torch', 'mindsdb']\n"
                    "for m in modules:\n"
                    "    try:\n"
                    "        importlib.import_module(m)\n"
                    "        print(f'Imported {m}')\n"
                    "    except Exception as exc:\n"
                    "        print(f'Failed to import {m}: {exc}')\n"
                    "print('Reading input file...')\n"
                    "with open('input_audio.bin','rb') as f:\n"
                    "    audio_bytes = f.read()\n"
                    "print(f'Audio size: {len(audio_bytes)} bytes')\n"
                    "print('Connexion à MindsDB...')\n"
                    "print('OK: Simulation de connexion effectuée.')\n"
                )
                probe_result = await loop.run_in_executor(
                    None,
                    lambda: run_python_code_in_sandbox(sandbox, probe_code),
                )
                probe_out = format_run_output(probe_result)

                error_msg = (
                    install_result.get('error')
                    or probe_result.get('error')
                )

                return {
                    "install_stdout": install_out,
                    "stdout": probe_out,
                    "error": error_msg,
                }
            except Exception as se:  # pragma: no cover
                logger.error(f"Sandbox probe error: {se}")
                return {"install_stdout": "", "stdout": "", "error": str(se)}
            finally:
                try:
                    if sandbox is not None:
                        # Terminate the sandbox cleanly
                        sandbox.kill()
                except Exception:
                    pass

        # Run the async sandbox interaction
        outputs = asyncio.run(_sandbox_mindsdb_probe(audio_bytes))

        return jsonify({
            "status": "real_endpoint_hit",
            "sandbox_install_stdout": outputs.get("install_stdout", ""),
            "sandbox_stdout": outputs.get("stdout", ""),
            "sandbox_error": outputs.get("error"),
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
    # Reuse validated settings for host/port
    app.run(
        host=settings.api_host,
        port=settings.api_port,
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )
