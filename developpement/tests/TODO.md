# Test TODOs

- [ ] Add unit tests for `AudioProcessor.process_audio_data` in `src/core/audio/processor.py` to exercise the full feature extraction pipeline. Mock `librosa`/`soundfile` to deliver deterministic audio arrays and assert both normal feature outputs and fallback default values when conversion fails.
