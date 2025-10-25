import base64
import textwrap

script = textwrap.dedent(
    """\
import importlib
import importlib.util
import pathlib

sdk = importlib.import_module(\"mindsdb_sdk\")
site_packages = pathlib.Path(sdk.__file__).resolve().parent.parent
alias_pkg = site_packages / \"mindsdb\"
alias_pkg.mkdir(exist_ok=True)
alias_init = alias_pkg / \"__init__.py\"

metadata_module = importlib.import_module(\"importlib.metadata\") if importlib.util.find_spec(\"importlib.metadata\") else None
version = metadata_module.version(\"mindsdb_sdk\") if metadata_module else getattr(sdk, \"__version__\", \"0.0.0\")

alias_init.write_text(
    \"import mindsdb_sdk as _sdk\\n\"
    \"_globals = {name: getattr(_sdk, name) for name in dir(_sdk) if not name.startswith('_')}\\n\"
    \"locals().update(_globals)\\n\"
    \"__all__ = [name for name in _globals]\\n\"
    f\"__version__ = '{version}'\\n\"
)
"""
)

print(base64.b64encode(script.encode()).decode())
