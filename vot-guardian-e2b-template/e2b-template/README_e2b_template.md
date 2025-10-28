# E2B Dockerfile Templates

This folder contains Dockerfile-based E2B templates with different sizes and startup trade-offs. Use the smallest template that fits your needs to keep sandbox creation fast under the 1-hour cloud builder limit.

Templates:

- e2b.Dockerfile.min → alias: vot-guardian-cpu-min
  - Includes: Python 3.10.11, torch==2.1.0 (CPU), numpy==1.26.4
  - Excludes: librosa, MindsDB server, ffmpeg, other heavy libs
  - Status: Built successfully (recommended baseline)

- e2b.Dockerfile.mid → alias: vot-guardian-cpu-mid
  - Includes: Python 3.10.11, torch==2.1.0 (CPU), numpy==1.26.4, librosa==0.10.1
  - System deps: libsndfile1 only (no ffmpeg)
  - Goal: add audio feature extraction without bloating build time
  
  When to use:
  - Simple audio feature extraction (mel-spectrograms, MFCCs) or loading WAVs
  - No Whisper or MindsDB server needed
  - Keep < 1h builder constraint easily
  
  Usage:
  - Python: `Sandbox.create('vot-guardian-cpu-mid')`
  - JS: `await Sandbox.create('vot-guardian-cpu-mid')`
  - CI: set `E2B_TEMPLATE_ALIAS=vot-guardian-cpu-mid`

- e2b.Dockerfile.fast → alias: vot-guardian-cpu-fast (candidate)
  - Intended: + librosa and audio basics
  - Note: This variant may exceed the 1-hour builder limit depending on system deps; use only if needed

- e2b.Dockerfile → alias: vot-guardian-cpu (full, heavy)
  - Intended: Adds curated MindsDB server runtime deps, Whisper, ffmpeg, librosa
  - Note: Heavier image; prefer local builds or longer E2B builder windows

Usage examples (create sandbox from a template alias):

- Python:

  ```python
  from e2b import Sandbox, AsyncSandbox
  # sync
  sandbox = Sandbox.create('vot-guardian-cpu-min')
  # async
  sandbox = await AsyncSandbox.create('vot-guardian-cpu-min')
  ```

- JavaScript:

  ```javascript
  import { Sandbox } from 'e2b'
  const sandbox = await Sandbox.create('vot-guardian-cpu-min')
  ```

Notes:

- If you need librosa in a minimal sandbox, install it on demand inside the sandbox to avoid template bloat.
- If you need MindsDB, consider running it as a separate service or using the full template locally.

## Validation

- Minimal: run `tests/validate_min_template.py` with E2B_API_KEY set.
- Mid: run `tests/validate_mid_template.py` with E2B_API_KEY set.
- Full: run `tests/validate_full_template.py` with E2B_API_KEY set. Optionally set `POSTGRES_DSN` to check DB connectivity. Override the template via `E2B_TEMPLATE_ALIAS` (defaults to `vot-guardian-cpu`).
