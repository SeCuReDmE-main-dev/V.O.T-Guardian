import json
from e2b import Sandbox


CMD = (
    "python -c \""
    "import numpy as np, soundfile as sf, librosa; "
    "sr=16000; t=np.arange(sr); "
    "y=(0.1*np.sin(2*np.pi*440*t/sr)).astype('float32'); "
    "sf.write('tone.wav', y, sr); "
    "y2, sr2 = librosa.load('tone.wav', sr=None, mono=True); "
    "print('Librosa OK:', librosa.__version__, 'len:', len(y2), 'sr:', sr2)"
    "\""
)


def main():
    alias = 'vot-guardian-cpu-mid'
    sb = Sandbox.create(alias)
    try:
        res = sb.commands.run(CMD)
        out = getattr(res, "stdout", None)
        if out is None:
            try:
                out = json.dumps(res)
            except Exception:
                out = str(res)
        print(out)
    finally:
        sb.kill()


if __name__ == "__main__":
    main()
