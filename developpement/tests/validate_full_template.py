def main():
import os
import sys
import json
import pathlib

# Minimal validation that runs inside an E2B sandbox
# and reports whether core libs are present and versions.

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))



    try:
        from e2b import Sandbox
    except Exception as exc:
        print(json.dumps({
            "error": f"e2b SDK not available: {exc}",
        }))
        return

    try:
        from src.core.e2b.sandbox_manager import run_python_code_in_sandbox
    except Exception as exc:
        print(json.dumps({
            "error": f"Import helper failed: {exc}",
        }))
        return

    template = os.getenv("E2B_TEMPLATE_ID", "vot-guardian-cpu-mid")
    sb = None
    try:
        sb = Sandbox(template=template)

        code = (
            "import json\n"
            "info = {}\n"
            "def safe_import(name):\n"
            "    try:\n"
            "        mod = __import__(name)\n"
            "        ver = getattr(mod, '__version__', 'unknown')\n"
            "        return True, ver\n"
            "    except Exception as err:\n"
            "        return False, str(err)\n"
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

        run_result = run_python_code_in_sandbox(sb, code)
        if run_result.get('error'):
            print(json.dumps({
                "error": run_result['error'],
            }))
            return

        if run_result.get('exit_code') not in (0, None):
            print(json.dumps({
                "error": "Sandbox script exited with non-zero code",
                "exit_code": run_result.get('exit_code'),
                "stdout": run_result.get('stdout', ''),
                "stderr": run_result.get('stderr', ''),
            }))
            return

        text = (run_result.get('stdout') or '').strip()
        if not text and run_result.get('stderr'):
            text = str(run_result['stderr']).strip()
        print(text)
    finally:
        try:
            if sb is not None:
                sb.kill()
        except Exception:
            pass


if __name__ == "__main__":
    main()
