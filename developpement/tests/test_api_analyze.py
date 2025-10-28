"""Integration test for the /analyze API endpoint."""

import io
import math
import struct
import wave
from contextlib import asynccontextmanager

import pytest

from src.api import main as api_main


FEATURE_KEYS = (
    "vot",
    "jitter",
    "snr_db",
    "shimmer",
    "mfcc_mean",
    "thd_percent",
    "spectral_centroid",
    "zero_crossing_rate",
)


class DummyAudioProcessor:
    def validate_audio_format(self, audio_bytes: bytes) -> bool:
        return True

    def process_audio_data(self, audio_bytes: bytes):
        return {
            key: index * 0.1 + 0.4
            for index, key in enumerate(FEATURE_KEYS)
        }


class DummyMLPredictor:
    async def predict(self, features):
        return {
            "prediction": "AI",
            "confidence": 0.93,
            "probabilities": [[0.07, 0.93]],
            "processing_time_ms": 12.3,
            "model_version": "test-model",
        }


class DummyDatadog:
    def record_analysis_metrics(self, *args, **kwargs):
        return None

    def record_audio_quality_metrics(self, *args, **kwargs):
        return None

    def record_tenebris_metrics(self, *args, **kwargs):
        return None


class DummyDBClient:
    pool = object()

    async def connect(self):
        return None

    async def store_analysis_result(self, payload):
        self.last_payload = payload

    async def log_audit_event(self, *args, **kwargs):
        self.last_audit = (args, kwargs)


@asynccontextmanager
async def _tenebris_context(call_id: str):
    yield "sandbox-dummy"


class DummyTenebris:
    def execute_protocol(self, call_id: str):
        return _tenebris_context(call_id)


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(api_main, "audio_processor", DummyAudioProcessor())
    monkeypatch.setattr(api_main, "ml_predictor", DummyMLPredictor())
    monkeypatch.setattr(api_main, "datadog", DummyDatadog())
    monkeypatch.setattr(api_main, "tenebris", DummyTenebris())
    monkeypatch.setattr(api_main, "db_client", DummyDBClient())

    return api_main.app.test_client()


def _build_test_audio(duration_seconds: float = 1.0) -> bytes:
    sample_rate = 16000
    frequency = 440
    amplitude = 16000
    total_frames = int(sample_rate * duration_seconds)

    frames = bytearray()
    for i in range(total_frames):
        sample = int(
            amplitude * math.sin(2 * math.pi * frequency * i / sample_rate)
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


def test_analyze_endpoint_returns_expected_payload(client):
    audio_bytes = _build_test_audio()
    response = client.post(
        "/analyze",
        data={"audio": (io.BytesIO(audio_bytes), "test.wav")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None

    assert payload["prediction"] == "AI"
    assert pytest.approx(payload["confidence"], 0.01) == 0.93

    features = payload["features"]
    assert isinstance(features, dict)
    for key in FEATURE_KEYS:
        assert key in features

    assert payload["tenebris_session"] == "sandbox-dummy"
    assert payload["status"] == "success"

