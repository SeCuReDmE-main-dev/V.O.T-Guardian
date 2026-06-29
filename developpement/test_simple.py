#!/usr/bin/env python3
"""
Simple V.O.T. Guardian Setup Test
=================================

Tests basic functionality without external dependencies.
"""

import sys
import os
from pathlib import Path

def test_basic():
    """Test basic project structure."""
    print("Testing V.O.T. Guardian Setup...")
    print("=" * 40)

    # Test 1: Check if key files exist
    required_files = [
        'src/__init__.py',
        'src/api/main.py',
        'src/core/security/tenebris.py',
        'requirements.txt',
        '.env',
        'README.md'
    ]

    missing = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"[OK] {file_path}")
        else:
            print(f"[FAIL] {file_path}")
            missing.append(file_path)

    # Test 2: Check .env.example content
    env_example = Path('.env.example')
    if env_example.exists():
        content = env_example.read_text()
        if 'E2B_API_KEY=placeholder_e2b_key' in content:
            print("[OK] E2B API key placeholder found")
        else:
            print("[FAIL] E2B API key placeholder missing")

        if 'DD_API_KEY=placeholder_datadog_key' in content:
            print("[OK] Datadog API key placeholder found")
        else:
            print("[FAIL] Datadog API key placeholder missing")

        if 'REDHAT_API_KEY=placeholder_redhat_key' in content:
            print("[OK] Red Hat API key placeholder found")
        else:
            print("[FAIL] Red Hat API key placeholder missing")
    else:
        print("[FAIL] .env.example file missing")

    # Test 3: Check requirements.txt
    req_file = Path('requirements.txt')
    if req_file.exists():
        content = req_file.read_text()
        if 'e2b-code-interpreter' in content:
            print("[OK] E2B dependency in requirements.txt")
        else:
            print("[FAIL] E2B dependency missing in requirements.txt")

        if 'datadog-api-client' in content:
            print("[OK] Datadog dependency in requirements.txt")
        else:
            print("[FAIL] Datadog dependency missing in requirements.txt")

        if 'cryptography' in content:
            print("[OK] Cryptography dependency in requirements.txt")
        else:
            print("[FAIL] Cryptography dependency missing in requirements.txt")
    else:
        print("[FAIL] requirements.txt file missing")

    # Summary
    print("\n" + "=" * 40)
    if not missing:
        print("SUCCESS: Project structure is complete!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env")
        print("2. Get API keys from:")
        print("   - E2B: https://e2b.dev")
        print("   - Datadog: https://datadoghq.com")
        print("   - Red Hat: https://developers.redhat.com/register")
        print("3. Install dependencies: pip install -r requirements.txt")
        print("4. Run: python -m src.api.main")
        return True
    else:
        print(f"FAILURE: {len(missing)} files missing")
        for file in missing:
            print(f"  - {file}")
        return False

if __name__ == "__main__":
    success = test_basic()
    sys.exit(0 if success else 1)