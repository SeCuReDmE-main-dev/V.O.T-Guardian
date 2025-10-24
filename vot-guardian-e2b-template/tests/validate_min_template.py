import json
from e2b import Sandbox


SCRIPT = (
    "python -c \"import torch, numpy as np; "
    "print('Torch OK:', torch.__version__); "
    "print('Numpy OK:', np.__version__)\""
)


def main():
    sb = Sandbox.create("vot-guardian-cpu-min")
    try:
        res = sb.commands.run(SCRIPT)
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
