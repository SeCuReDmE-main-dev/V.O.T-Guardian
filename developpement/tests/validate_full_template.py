import os
import json

# Minimal validation that runs inside an E2B sandbox
# and reports whether core libs are present and versions.


def main():
    try:
        from e2b import Sandbox
    except Exception as e:
        print(json.dumps({
            "error": f"e2b SDK not available: {e}",
        }))
        return

    template = os.getenv("E2B_TEMPLATE_ID", "vot-guardian-cpu-mid")
    sb = None
    try:
        sb = Sandbox.create(template)

        code = (
            "import json\n"
            "info = {}\n"
            "def safe_import(name):\n"
            "    try:\n"
            "        mod = __import__(name)\n"
            "        ver = getattr(mod, '__version__', 'unknown')\n"
            "        return True, ver\n"
            "    except Exception as e:\n"
            "        return False, str(e)\n"
            "ok_torch, v_torch = safe_import('torch')\n"
            "ok_librosa, v_librosa = safe_import('librosa')\n"
            "ok_mdb, v_mdb = safe_import('mindsdb')\n"
            "ok_whisper, v_whisper = safe_import('whisper')\n"
            "print(json.dumps({\n"
            "  'torch': {'ok': ok_torch, 'version': v_torch},\n"
            "  'librosa': {'ok': ok_librosa, 'version': v_librosa},\n"
            "  'mindsdb': {'ok': ok_mdb, 'version': v_mdb},\n"
            "  'whisper': {'ok': ok_whisper, 'version': v_whisper},\n"
            "}))\n"
        )
        res = sb.run_code(code)
        out = getattr(getattr(res, 'logs', None), 'stdout', None)
        text = "\n".join(out) if out else getattr(res, 'text', '')
        print(text.strip())
    finally:
        try:
            if sb is not None:
                sb.kill()
        except Exception:
            pass


if __name__ == "__main__":
    main()
