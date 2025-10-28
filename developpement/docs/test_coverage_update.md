# Test Coverage Update (2025-10-28)

- Commands executed:
  - `python -m pytest --maxfail=3 --disable-warnings`
  - `python -m pytest --cov=src --cov-report=term-missing`
- Overall coverage: **52%** (524 lines missing out of 1082)
- New targeted tests: `tests/test_ml_predictor.py::test_predict_high_confidence_ai`, `tests/test_ml_predictor.py::test_predict_fallback_when_model_missing`, and `tests/test_pipeline_e2e.py::test_pipeline_e2e_persists_features`

## Newly Covered Paths

- `src/core/audio/processor.AudioProcessor.process_audio_data` happy-path computation across feature extractors.
- Error fallback branch for `AudioProcessor.process_audio_data` ensuring default metrics are returned when decoding fails.
- `tests/test_setup.py` now uses assertions/skip logic, eliminating legacy return-value warnings.

## Remaining Low-Coverage Modules

- `src/core/database/postgresql_client.py` (43%): persistence lifecycle, retry logic, and error handling still untested.
- `src/core/e2b/sandbox_manager.py` (25%): sandbox orchestration flows, timeout paths, and cleanup remain uncovered.
- `src/core/ml/predictor.py` (60%): model loading edge cases, GPU/mixed precision paths, and drift detection remain untested.
- `src/core/monitoring/datadog_client.py` (42%): metric batching and error telemetry code paths lack coverage.
- `src/core/security/tenebris.py` (43%): session validation and audit hooks are not exercised.

## Immediate Plan

1. Target `DatadogClient` metrics emission with stub transport to exercise success/failure branches.
2. Add sandbox lifecycle tests in `E2BSandboxManager` to cover session creation and cleanup (mocking E2B SDK).
3. Follow up with persistence integration tests around `PostgreSQLClient` once database fixtures are available.
