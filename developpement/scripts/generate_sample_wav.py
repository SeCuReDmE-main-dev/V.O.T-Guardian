import wave
import struct
import math


def write_sine_wav(
    path: str,
    seconds: float = 1.0,
    freq: float = 440.0,
    samplerate: int = 16000,
    amplitude: int = 16000,
):
    frames = int(seconds * samplerate)
    with wave.open(path, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(samplerate)
        for i in range(frames):
            phase = 2 * math.pi * freq * (i / samplerate)
            val = int(amplitude * math.sin(phase))
            f.writeframes(struct.pack('<h', val))


if __name__ == '__main__':
    write_sine_wav('sample_audio.wav', seconds=1.0, freq=440.0)
    print('Wrote sample_audio.wav')
