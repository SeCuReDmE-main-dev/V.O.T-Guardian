"""Manual integration test for the /analyze endpoint."""

import io
import struct
import sys
import wave
import logging
sample_rate = 16000
frequency = 440
seconds = 1.0
amplitude = 16000

total_frames = int(sample_rate * seconds)
frames = bytearray()
for i in range(total_frames):
    sample = int(
        amplitude * math.sin(2 * math.pi * frequency * i / sample_rate)
    )
    frames.extend(struct.pack("<h", sample))

audio_buffer = io.BytesIO()
with wave.open(audio_buffer, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    wf.writeframes(frames)

audio_buffer.seek(0)
audio_bytes = audio_buffer.read()


def main() -> None:
    import sys

    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    SRC_PATH = PROJECT_ROOT / "src"
    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))

    from flask.testing import FlaskClient

    from api.main import app, logger as api_logger  # type: ignore

    # Configure logging to ensure visibility during the manual run.
    logging.basicConfig(level=logging.DEBUG)
    api_logger.setLevel(logging.DEBUG)

    client: FlaskClient = app.test_client()
    response = client.post(
        "/analyze",
        data={"audio": (io.BytesIO(audio_bytes), "test.wav")},
        content_type="multipart/form-data",
    )

    print("Status:", response.status_code)
    print("JSON:", response.get_json())


if __name__ == "__main__":
    main()
