"""Tests for :class:`MLPredictor` async inference paths."""

import pytest
from src.core.ml.predictor import MLPredictor, ModelConfig


torch = pytest.importorskip("torch")


@pytest.fixture
def anyio_backend():
    return "asyncio"


class _StubModel:
    def __init__(self, logits):
        self._logits = logits

    def __call__(self, _):
        return self._logits


@pytest.mark.anyio
async def test_predict_high_confidence_ai(monkeypatch):
    monkeypatch.setattr(MLPredictor, "load_model", lambda self: None)

    config = ModelConfig(use_gpu=False, mixed_precision=False)
    predictor = MLPredictor(config=config)
    predictor.model = _StubModel(torch.tensor([[0.2, 2.3]]))

    features = {
        "vot": 0.45,
        "jitter": 0.02,
        "shimmer": 0.08,
        "snr_db": 28.0,
        "thd_percent": 0.6,
        "mfcc_mean": 0.15,
    }

    result = await predictor.predict(features)

    assert result["prediction"] == "AI"
    assert result["confidence"] == pytest.approx(0.90, abs=0.05)
    assert result["probabilities"][0][1] > result["probabilities"][0][0]
    assert result["features_used"] == list(features.keys())


@pytest.mark.anyio
async def test_predict_fallback_when_model_missing(monkeypatch):
    monkeypatch.setattr(MLPredictor, "load_model", lambda self: None)

    config = ModelConfig(use_gpu=False, mixed_precision=False)
    predictor = MLPredictor(config=config)
    predictor.model = None

    result = await predictor.predict({})

    assert result["prediction"] == "HUMAN"
    assert result["confidence"] == pytest.approx(0.5, abs=1e-9)
    assert "error" in result
    assert "probabilities" not in result
