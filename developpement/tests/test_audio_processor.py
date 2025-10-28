"""Unit tests for :class:`AudioProcessor` orchestrations and fallbacks."""

import types

import numpy as np
import pytest

from src.core.audio import processor as audio_module
from src.core.audio.processor import AudioProcessor


def test_process_audio_data_nominal(monkeypatch):
    processor = AudioProcessor()
    sample_rate = processor.config.sample_rate
    audio_array = np.sin(np.linspace(0, 2 * np.pi, sample_rate))
    audio_array = audio_array.astype(np.float32)

    soundfile_stub = types.SimpleNamespace(
        read=lambda buffer: (audio_array.copy(), sample_rate)
    )
    monkeypatch.setattr(audio_module, "sf", soundfile_stub)

    feature_stub = types.SimpleNamespace(
        zero_crossing_rate=lambda audio: np.array([[0.1, 0.2, 0.1]]),
        spectral_centroid=lambda y, sr: np.array([[400.0, 500.0, 600.0]]),
        mfcc=lambda y, sr, n_mfcc: np.full((n_mfcc, 3), 0.3, dtype=float),
    )

    monkeypatch.setattr(
        audio_module,
        "librosa",
        types.SimpleNamespace(
            piptrack=lambda y, sr: (
                np.array([[0.0, 0.0, 0.0], [220.0, 221.0, 219.0]]),
                np.array([[0.0, 0.0, 0.0], [1.0, 0.8, 1.1]]),
            ),
            resample=lambda y, orig_sr, target_sr: y,
            feature=feature_stub,
        ),
    )

    monkeypatch.setattr(
        audio_module,
        "welch",
        lambda audio, sample_rate, nperseg=1024: (
            np.array([100.0, 200.0, 300.0, 400.0]),
            np.array([10.0, 5.0, 2.0, 1.0]),
        ),
    )

    audio_bytes = b"nominal-audio"
    expected_audio, expected_rate = processor._bytes_to_array(audio_bytes)

    expected_features = {
        "vot": processor._extract_vot(expected_audio, expected_rate),
        "jitter": processor._calculate_jitter(expected_audio, expected_rate),
        "shimmer": processor._calculate_shimmer(expected_audio),
        "snr_db": processor._calculate_snr(expected_audio),
        "thd_percent": processor._calculate_thd(
            expected_audio,
            expected_rate,
        ),
        "zero_crossing_rate": processor._calculate_zero_crossing_rate(
            expected_audio,
        ),
        "spectral_centroid": processor._calculate_spectral_centroid(
            expected_audio,
            expected_rate,
        ),
        "mfcc_mean": processor._calculate_mfcc_mean(
            expected_audio,
            expected_rate,
        ),
    }

    result = processor.process_audio_data(audio_bytes)

    assert set(result.keys()) == set(expected_features.keys())
    for key, expected_value in expected_features.items():
        assert result[key] == pytest.approx(expected_value, rel=1e-6)


def test_process_audio_data_fallback(monkeypatch):
    processor = AudioProcessor()

    def raising_bytes_to_array(_):
        raise RuntimeError("decoding failure")

    monkeypatch.setattr(processor, "_bytes_to_array", raising_bytes_to_array)

    logged = {}

    def fake_error(message):
        logged["message"] = message

    monkeypatch.setattr(processor.logger, "error", fake_error)

    result = processor.process_audio_data(b"")

    assert result == {
        "vot": 0.4,
        "jitter": 0.05,
        "shimmer": 0.1,
        "snr_db": 20.0,
        "thd_percent": 1.0,
        "zero_crossing_rate": 0.1,
        "spectral_centroid": 1000.0,
        "mfcc_mean": 0.0,
    }
    assert "Error processing audio" in logged["message"]
