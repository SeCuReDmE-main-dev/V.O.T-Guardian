# Test TODOs

- [x] Add unit tests for `MLPredictor.predict` in `src/core/ml/predictor.py`, mocking Torch tensors to verify probability normalization, confidence threshold enforcement, and fallback behavior when the model reports low confidence.
- [ ] Cover `DatadogClient` metric emission in `src/core/monitoring/datadog_client.py` with stubbed HTTP transport to assert success/error logging paths.
