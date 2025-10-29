# Coverage Snapshot - 2025-10-28

Command: `PYTHONPATH=. pytest --cov=src --cov-report=term-missing`

| Module | Stmts | Miss | Cover | Key Missing Ranges |
| --- | ---: | ---: | ---: | --- |
| src/__init__.py | 9 | 0 | 100% | - |
| src/api/main.py | 125 | 28 | 78% | 35-41, 97, 109, 166-177, 212-305, 322-363 |
| src/config/settings.py | 53 | 12 | 77% | 71-92, 114-127, 146, 161 |
| src/core/audio/processor.py | 174 | 58 | 67% | 28-30, 56, 104-191, 207-340 |
| src/core/database/postgresql_client.py | 98 | 35 | 64% | 60-133, 218-253, 310, 334-364 |
| src/core/e2b/sandbox_manager.py | 244 | 116 | 52% | 75-134, 246-533 |
| src/core/ml/predictor.py | 179 | 72 | 60% | 30-36, 116-458 |
| src/core/monitoring/datadog_client.py | 109 | 63 | 42% | 30-31, 66-290 |
| src/core/security/tenebris.py | 91 | 52 | 43% | 75-255 |
| __TOTAL__ | __1082__ | __436__ | __60%__ | - |

## Under-tested modules (<50% coverage)

- `src/core/monitoring/datadog_client.py` - 42%: metric/event dispatch paths (success, retries, API key failure) remain unverified.
- `src/core/security/tenebris.py` - 43%: cryptographic policy enforcement and fallback handling lack regression coverage.

## Immediate focus

1. Land unit tests for Datadog metric batching and error logging (blocked by pending client stubs).
2. Stub Tenebris policy loader to exercise compliance fallbacks and exception recovery paths.
3. Extend sandbox manager scenarios to cover scaling/health-check branches and promote coverage past 70%.
