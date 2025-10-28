"""End-to-end pipeline test ensuring persistence and ML prediction wiring."""

import io
import json
import math
import struct
import wave

import pytest

from src.api import main as api_main


FEATURES = {
    "vot": 0.41,
    "jitter": 0.03,
    "shimmer": 0.07,
    "snr_db": 26.5,
    "thd_percent": 0.9,
    "zero_crossing_rate": 0.12,
    "spectral_centroid": 520.0,
    "mfcc_mean": 0.11,
}


class DummyAudioProcessor:
    def __init__(self):
        self.last_audio = None

    def validate_audio_format(self, audio_bytes: bytes) -> bool:
        self.last_audio = audio_bytes
        return True

    def process_audio_data(self, audio_bytes: bytes):
        self.last_audio = audio_bytes
        return FEATURES.copy()


class DummyMLPredictor:
    def __init__(self):
        self.invocations = 0
        self.seen_features = None

    async def predict(self, features):
        self.invocations += 1
        self.seen_features = features
        return {
            "prediction": "AI",
            "confidence": 0.88,
            "probabilities": [[0.12, 0.88]],
            "processing_time_ms": 8.2,
            "model_version": "test-model",
        }


class DummyDatadog:
    def record_analysis_metrics(self, **kwargs):
        return None

    def record_audio_quality_metrics(self, **kwargs):
        return None

    def record_tenebris_metrics(self, **kwargs):
        return None


class DummyDBClient:
    def __init__(self):
        self.pool = object()
        self.last_analysis = None
        self.audit_events = []

    async def connect(self):
        return None

    async def store_analysis_result(self, payload):
        self.last_analysis = payload

    async def log_audit_event(self, **kwargs):
        self.audit_events.append(kwargs)


class DummyTenebris:
    async def __aenter__(self):
        return "sandbox-dummy"

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def execute_protocol(self, call_id: str):
        return self


def _build_audio(duration_seconds: float = 0.5) -> bytes:
    sample_rate = 16000
    frequency = 440
    amplitude = 10000
    total_frames = int(sample_rate * duration_seconds)

    frames = bytearray()
    for index in range(total_frames):
        sample = int(
            amplitude * math.sin(2 * math.pi * frequency * index / sample_rate)
        )
        frames.extend(struct.pack("<h", sample))

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)

    buffer.seek(0)
    return buffer.read()


@pytest.fixture()
def pipeline_client(monkeypatch):
    audio_processor = DummyAudioProcessor()
    ml_predictor = DummyMLPredictor()
    datadog = DummyDatadog()
    db_client = DummyDBClient()
    tenebris = DummyTenebris()

    monkeypatch.setattr(api_main, "audio_processor", audio_processor)
    monkeypatch.setattr(api_main, "ml_predictor", ml_predictor)
    monkeypatch.setattr(api_main, "datadog", datadog)
    monkeypatch.setattr(api_main, "db_client", db_client)
    monkeypatch.setattr(api_main, "tenebris", tenebris)

    client = api_main.app.test_client()
    return {
        "client": client,
        "audio_processor": audio_processor,
        "ml_predictor": ml_predictor,
        "db_client": db_client,
    }


def test_pipeline_e2e_persists_features(pipeline_client):
    context = pipeline_client
    audio_bytes = _build_audio()

    response = context["client"].post(
        "/analyze",
        data={"audio": (io.BytesIO(audio_bytes), "sample.wav")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()

    assert payload["prediction"] == "AI"
    assert payload["confidence"] == pytest.approx(0.88, abs=1e-6)
    stored_features = json.loads(
        context["db_client"].last_analysis["features"]
    )
    assert stored_features == FEATURES
    assert context["ml_predictor"].invocations == 1
    assert context["ml_predictor"].seen_features == FEATURES
    last_audit = context["db_client"].audit_events[-1]
    assert last_audit["event_type"] == "ANALYSIS_COMPLETED"
    assert last_audit["call_id"] == payload["call_id"]
