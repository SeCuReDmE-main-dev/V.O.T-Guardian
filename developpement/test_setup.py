#!/usr/bin/env python3
"""
V.O.T. Guardian - Setup Functionality Test
==========================================

Tests if the core components can be imported and initialized
without requiring API keys or running databases.

Usage: python test_setup.py
"""

import importlib.util
import sys
from pathlib import Path
from typing import List, Tuple

import pytest

MODULES_TO_TEST = [
    "src",
    "src.api.main",
    "src.core.security.tenebris",
    "src.core.monitoring.datadog_client",
    "src.core.e2b.sandbox_manager",
    "src.core.audio.processor",
    "src.core.ml.predictor",
    "src.core.database.postgresql_client",
    "src.config.settings",
]

DEPENDENCIES = [
    ("e2b-code-interpreter", "E2B sandbox isolation"),
    ("datadog-api-client", "Datadog monitoring"),
    ("cryptography", "Encryption for Tenebris"),
]

ENV_PLACEHOLDERS = [
    "E2B_API_KEY=your_e2b_api_key_here",
    "DD_API_KEY=your_datadog_api_key_here",
    "REDHAT_API_KEY=your_redhat_api_key_here",
]

REQUIRED_FILES = [
    "src/__init__.py",
    "src/api/main.py",
    "src/core/security/tenebris.py",
    "src/core/monitoring/datadog_client.py",
    "src/core/e2b/sandbox_manager.py",
    "src/core/audio/processor.py",
    "src/core/ml/predictor.py",
    "src/core/database/postgresql_client.py",
    "src/config/settings.py",
    "requirements.txt",
    "docker-compose.yml",
    "README.md",
]


def _check_module_imports(verbose: bool = True) -> Tuple[bool, List[Tuple[str, str]]]:
    if verbose:
        print("[TEST] Testing core module imports...")

    failed_imports: List[Tuple[str, str]] = []

    for module_name in MODULES_TO_TEST:
        try:
            if module_name == "src":
                spec = importlib.util.spec_from_file_location("src", "src/__init__.py")
                if not spec or not spec.loader:
                    raise ImportError("Unable to load src package spec")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                __import__(module_name, fromlist=[""])

            if verbose:
                print(f"  ✅ {module_name}")
        except Exception as exc:
            if verbose:
                print(f"  ❌ {module_name}: {exc}")
            failed_imports.append((module_name, str(exc)))

    return len(failed_imports) == 0, failed_imports


def _check_dependency_status(verbose: bool = True) -> Tuple[List[str], List[str]]:
    if verbose:
        print("\n🔧 Testing core dependencies...")

    available: List[str] = []
    missing: List[str] = []

    for dep_name, description in DEPENDENCIES:
        import_name = dep_name.replace("-", "_")
        try:
            __import__(import_name)
            available.append(dep_name)
            if verbose:
                print(f"  ✅ {dep_name} ({description})")
        except ImportError as exc:
            missing.append(dep_name)
            if verbose:
                print(f"  ⚠️ {dep_name}: Not installed ({exc})")

    return available, missing


def _validate_configuration(verbose: bool = True) -> Tuple[bool, str | None]:
    if verbose:
        print("\n⚙️ Testing configuration...")

    try:
        from src.config.settings import Settings

        settings = Settings()

        if verbose:
            print("  ✅ Settings loaded successfully")
            print(f"  ✅ API port: {settings.api_port}")
            print(f"  ✅ Max audio size: {settings.max_audio_file_size}")
            print(f"  ✅ Tenebris max time: {settings.tenebris_max_time_ms}ms")
            print(f"  ✅ ML confidence threshold: {settings.ml_confidence_threshold}")

            if settings.is_production_ready():
                print("  ⚠️ Configuration is production-ready")
            else:
                print("  ℹ️ Configuration needs API keys for production")

        return True, None

    except Exception as exc:
        if verbose:
            print(f"  ❌ Configuration test failed: {exc}")
        return False, str(exc)


def _inspect_env_example(verbose: bool = True) -> Tuple[bool, List[str]]:
    if verbose:
        print("\n🌍 Testing environment variables...")

    env_example = Path(".env.example")
    if not env_example.exists():
        if verbose:
            print("  ❌ .env.example file missing")
        return False, [".env.example missing"]

    if verbose:
        print("  ✅ .env.example file exists")

    missing_placeholders: List[str] = []
    content = env_example.read_text()

    for placeholder in ENV_PLACEHOLDERS:
        key = placeholder.split("=")[0]
        if placeholder in content:
            if verbose:
                print(f"  ✅ {key} placeholder found")
        else:
            if verbose:
                print(f"  ❌ {key} placeholder missing")
            missing_placeholders.append(key)

    return len(missing_placeholders) == 0, missing_placeholders


def _verify_project_structure(verbose: bool = True) -> Tuple[bool, List[str]]:
    if verbose:
        print("\n📁 Testing project structure...")

    missing_files: List[str] = []

    for file_path in REQUIRED_FILES:
        if Path(file_path).exists():
            if verbose:
                print(f"  ✅ {file_path}")
        else:
            if verbose:
                print(f"  ❌ {file_path}")
            missing_files.append(file_path)

    return len(missing_files) == 0, missing_files


def test_imports():
    imports_ok, failures = _check_module_imports(verbose=False)
    assert imports_ok, f"Module import failures: {failures}"


def test_dependencies():
    available, missing = _check_dependency_status(verbose=False)
    if missing:
        pytest.skip(f"Optional dependencies missing: {', '.join(missing)}")
    assert available, "No optional dependencies installed"


def test_configuration():
    config_ok, error = _validate_configuration(verbose=False)
    assert config_ok, f"Configuration failed: {error}"


def test_environment_variables():
    env_ok, missing = _inspect_env_example(verbose=False)
    assert env_ok, f"Missing environment placeholders: {missing}"


def test_project_structure():
    structure_ok, missing = _verify_project_structure(verbose=False)
    assert structure_ok, f"Missing project files: {missing}"


def main() -> int:
    print("🚀 V.O.T. Guardian - Setup Functionality Test")
    print("=" * 50)

    imports_ok, import_failures = _check_module_imports()
    available_deps, missing_deps = _check_dependency_status()
    config_ok, config_error = _validate_configuration()
    env_ok, missing_env = _inspect_env_example()
    structure_ok, missing_files = _verify_project_structure()

    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    all_passed = all([imports_ok, config_ok, env_ok, structure_ok])

    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Your V.O.T. Guardian setup is functional!")
        print("\nNext steps:")
        print("1. 📝 Copy .env.example to .env")
        print("2. 🔑 Get your API keys:")
        print("   • E2B: https://e2b.dev")
        print("   • Datadog: https://datadoghq.com")
        print("   • Red Hat: https://developers.redhat.com")
        print("3. 🗄️ Install databases (PostgreSQL, RethinkDB, MindsDB)")
        print("4. 🚀 Run: python -m src.api.main")
    else:
        print("⚠️ SOME TESTS FAILED")
        print("\nIssues to fix:")

        if import_failures:
            print(f"  • Import errors: {len(import_failures)} modules")
            for module, error in import_failures:
                print(f"    - {module}: {error}")

        if missing_files:
            print(f"  • Missing files: {len(missing_files)} files")
            for file_path in missing_files:
                print(f"    - {file_path}")

        if missing_env:
            print(
                "  • Missing environment placeholders: "
                + ", ".join(missing_env)
            )

        if not config_ok and config_error:
            print(f"  • Configuration error: {config_error}")

    if missing_deps:
        print("\nOptional dependencies not installed:")
        for dep_name in missing_deps:
            print(f"  - {dep_name}")

    print("\n🔗 For Red Hat API Key:")
    print("   Recommended: Red Hat Developer Subscription (FREE)")
    print("   URL: https://developers.redhat.com/register")
    print("   Includes: RHEL, OpenShift Developer Sandbox, Podman")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
V.O.T. Guardian - Setup Functionality Test
==========================================

Tests if the core components can be imported and initialized
without requiring API keys or running databases.

Usage: python test_setup.py
"""

import sys
import os
import importlib.util
from pathlib import Path

def test_imports():
    """Test if all core modules can be imported."""
    print("[TEST] Testing core module imports...")

    modules_to_test = [
        'src',
        'src.api.main',
        'src.core.security.tenebris',
        'src.core.monitoring.datadog_client',
        'src.core.e2b.sandbox_manager',
        'src.core.audio.processor',
        'src.core.ml.predictor',
        'src.core.database.postgresql_client',
        'src.config.settings'
    ]

    failed_imports = []

    for module_name in modules_to_test:
        try:
            # Try to import the module
            if module_name == 'src':
                # Special case for src package
                spec = importlib.util.spec_from_file_location("src", "src/__init__.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                # Regular module import
                module = __import__(module_name, fromlist=[''])

            print(f"  ✅ {module_name}")
        except Exception as e:
            print(f"  ❌ {module_name}: {e}")
            failed_imports.append((module_name, str(e)))

    return len(failed_imports) == 0, failed_imports

def test_dependencies():
    """Test if core dependencies are available."""
    print("\n🔧 Testing core dependencies...")

    dependencies = [
        ('e2b-code-interpreter', 'E2B sandbox isolation'),
        ('datadog-api-client', 'Datadog monitoring'),
        ('cryptography', 'Encryption for Tenebris')
    ]

    available_deps = []

    for dep_name, description in dependencies:
        try:
            # Try to import the dependency
            __import__(dep_name.replace('-', '_'))
            print(f"  ✅ {dep_name} ({description})")
            available_deps.append(dep_name)
        except ImportError as e:
            print(f"  ⚠️ {dep_name}: Not installed ({e})")

    return available_deps

def test_configuration():
    """Test configuration loading."""
    print("\n⚙️ Testing configuration...")

    try:
        from src.config.settings import Settings

        # Test with default values
        settings = Settings()

        print("  ✅ Settings loaded successfully")
        print(f"  ✅ API port: {settings.api_port}")
        print(f"  ✅ Max audio size: {settings.max_audio_file_size}")
        print(f"  ✅ Tenebris max time: {settings.tenebris_max_time_ms}ms")
        print(f"  ✅ ML confidence threshold: {settings.ml_confidence_threshold}")

        # Test production readiness check
        production_ready = settings.is_production_ready()
        if production_ready:
            print("  ⚠️ Configuration is production-ready")
        else:
            print("  ℹ️ Configuration needs API keys for production")

        return True

    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variable placeholders."""
    print("\n🌍 Testing environment variables...")

    # Check .env.example file exists
    env_example = Path('.env.example')
    if env_example.exists():
        print("  ✅ .env.example file exists")

        # Check for key placeholders
        content = env_example.read_text()
        required_vars = [
            'E2B_API_KEY=your_e2b_api_key_here',
            'DD_API_KEY=your_datadog_api_key_here',
            'REDHAT_API_KEY=your_redhat_api_key_here'
        ]

        for var in required_vars:
            if var in content:
                print(f"  ✅ {var.split('=')[0]} placeholder found")
            else:
                print(f"  ❌ {var.split('=')[0]} placeholder missing")

        return True
    else:
        print("  ❌ .env.example file missing")
        return False

def test_project_structure():
    """Test if project structure is complete."""
    print("\n📁 Testing project structure...")

    required_files = [
        'src/__init__.py',
        'src/api/main.py',
        'src/core/security/tenebris.py',
        'src/core/monitoring/datadog_client.py',
        'src/core/e2b/sandbox_manager.py',
        'src/core/audio/processor.py',
        'src/core/ml/predictor.py',
        'src/core/database/postgresql_client.py',
        'src/config/settings.py',
        'requirements.txt',
        'docker-compose.yml',
        'README.md'
    ]

    missing_files = []

    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            missing_files.append(file_path)

    return len(missing_files) == 0, missing_files

def main():
    """Run all tests."""
    print("🚀 V.O.T. Guardian - Setup Functionality Test")
    print("=" * 50)

    # Run tests
    import_tests_passed, import_failures = test_imports()
    deps_available = test_dependencies()
    config_test_passed = test_configuration()
    env_vars_ok = test_environment_variables()
    structure_ok, missing_files = test_project_structure()

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    all_passed = all([
        import_tests_passed,
        config_test_passed,
        env_vars_ok,
        structure_ok
    ])

    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Your V.O.T. Guardian setup is functional!")
        print("\nNext steps:")
        print("1. 📝 Copy .env.example to .env")
        print("2. 🔑 Get your API keys:")
        print("   • E2B: https://e2b.dev")
        print("   • Datadog: https://datadoghq.com")
        print("   • Red Hat: https://developers.redhat.com")
        print("3. 🗄️ Install databases (PostgreSQL, RethinkDB, MindsDB)")
        print("4. 🚀 Run: python -m src.api.main")

    else:
        print("⚠️ SOME TESTS FAILED")
        print("\nIssues to fix:")

        if import_failures:
            print(f"  • Import errors: {len(import_failures)} modules")
            for module, error in import_failures:
                print(f"    - {module}: {error}")

        if missing_files:
            print(f"  • Missing files: {len(missing_files)} files")
            for file in missing_files:
                print(f"    - {file}")

        if not deps_available:
            print("  • Missing dependencies: install with 'pip install -r requirements.txt'")

    print("\n🔗 For Red Hat API Key:")
    print("   Recommended: Red Hat Developer Subscription (FREE)")
    print("   URL: https://developers.redhat.com/register")
    print("   Includes: RHEL, OpenShift Developer Sandbox, Podman")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())