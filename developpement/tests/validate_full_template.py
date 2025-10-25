import importlib
import json
import os
import pathlib
import sys

# Minimal validation that runs inside an E2B sandbox and reports
# whether core libs are present together with their versions.

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _print_error(message: str) -> None:
    print(json.dumps({"error": message}))


def main() -> None:
    try:
        e2b_module = importlib.import_module("e2b")
        Sandbox = getattr(e2b_module, "Sandbox")
    except Exception as exc:  # pragma: no cover - import guard
        _print_error(f"e2b SDK not available: {exc}")
        return

    try:
        from src.core.e2b.sandbox_manager import run_python_code_in_sandbox
    except Exception as exc:  # pragma: no cover - import guard
        _print_error(f"Import helper failed: {exc}")
        return

    template = os.getenv("E2B_TEMPLATE_ID", "vot-guardian-cpu-mid")
    sandbox = None
    try:
        sandbox = Sandbox(template=template)

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

        run_result = run_python_code_in_sandbox(sandbox, code)
        if run_result.get("error"):
            _print_error(str(run_result["error"]))
            return

        if run_result.get("exit_code") not in (0, None):
            _print_error("Sandbox script exited with non-zero code")
            print(json.dumps({
                "stdout": run_result.get("stdout", ""),
                "stderr": run_result.get("stderr", ""),
            }))
            return

        output_text = (run_result.get("stdout") or "").strip()
        if not output_text and run_result.get("stderr"):
            output_text = str(run_result["stderr"]).strip()
        print(output_text)
    finally:
        if sandbox is not None:
            try:
                sandbox.kill()
            except Exception:
                pass


if __name__ == "__main__":
    main()
