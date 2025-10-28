# Test Coverage Report (2025-10-28)

- Command: `python -m pytest --cov=src --cov-report=term-missing`
- Overall coverage: **40%** (646 of 1082 lines missing)
- Test session: 8 passed, 3 skipped, 10 warnings

## Notable Coverage Gaps

| Module | Coverage | Key Missing Areas |
| --- | --- | --- |
| `src/api/main.py` | 78% | Error handling branches around lines 35-41, 97, 109, 166-167, 177, 212-213, 252, 269, 282, 289, 292, 297-305, 322, 333, 342, 354, 363 |
| `src/config/settings.py` | 81% | Optional configuration loaders at lines 71-92, 127, 146, 161 |
| `src/core/audio/processor.py` | 20% | Majority of signal processing pipeline (28-325, 329-340) |
| `src/core/database/postgresql_client.py` | 43% | Connection lifecycle and persistence paths (60-336, 340-364) |
| `src/core/e2b/sandbox_manager.py` | 25% | Sandbox orchestration logic (75-476, 480, 518-545) |
| `src/core/ml/predictor.py` | 36% | Model inference and post-processing (30-316, 325-458) |
| `src/core/monitoring/datadog_client.py` | 42% | Metric emission flows (30-290) |
| `src/core/security/tenebris.py` | 43% | Session management and validation (75-255) |

## Warnings Observed

- CUDA disabled warning from `torch.cuda.amp.GradScaler` (GPU not available).
- Several legacy tests in `test_setup.py` return values instead of using `assert`, causing `PytestReturnNotNoneWarning`.
- Async database smoke tests in `test_databases.py` are skipped because coroutine support plugins are absent.

## Next Steps

1. Prioritise targeted unit tests for `src/core/audio/processor.py` and `src/core/ml/predictor.py` as they drive the analyze pipeline.
2. Refine scaffold tests in `test_setup.py` to use assertions and eliminate return-value warnings.
3. Evaluate need for async test plugin (e.g. `pytest-asyncio`) if database coroutine tests should run instead of being skipped.
