import os
import json
from e2b import Sandbox


def main():
    alias = os.getenv("E2B_TEMPLATE_ALIAS", "vot-guardian-cpu")
    sb = Sandbox.create(alias)
    try:
        # Sanity: verify core libs and presence of optional ones
        cmd = (
            "python - << 'PY'\n"
            "import importlib, json\n"
            "import torch, librosa\n"
            "out = {\n"
            "  'torch': getattr(torch, '__version__', None),\n"
            "  'librosa': getattr(librosa, '__version__', None),\n"
            "  'mindsdb': bool(importlib.util.find_spec('mindsdb')),\n"
            "  'whisper': bool(importlib.util.find_spec('whisper')),\n"
            "}\n"
            "print(json.dumps(out))\n"
            "PY\n"
        )
        res = sb.commands.run(cmd)
        stdout = getattr(res, "stdout", "")
        print(stdout)
        try:
            payload = json.loads(stdout.strip())
        except Exception:
            payload = {}
        # Quick assertions-like prints
        print("Torch OK:", bool(payload.get("torch")))
        print("Librosa OK:", bool(payload.get("librosa")))
        print("MindsDB present:", payload.get("mindsdb"))
        print("Whisper present:", payload.get("whisper"))

        # Optional Postgres check
        pg_dsn = os.getenv("POSTGRES_DSN")
        if pg_dsn:
            # Escape single quotes for shell safety.
            safe_dsn = pg_dsn.replace("'", "\\'")
            script_pg = (
                "import psycopg\n"
                f"conn = psycopg.connect('{safe_dsn}')\n"
                "conn.close()\n"
                "print('Postgres OK')\n"
            )
            cmd_pg = (
                "python - << 'PY'\n" + script_pg + "PY\n"
            )
            res2 = sb.commands.run(cmd_pg)
            print(getattr(res2, "stdout", res2))
        else:
            print("POSTGRES_DSN not set - skipping DB check")
    finally:
        sb.kill()


if __name__ == "__main__":
    main()
