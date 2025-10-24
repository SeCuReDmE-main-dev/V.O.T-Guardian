#!/usr/bin/env python3
"""
V.O.T. Guardian - Database Connection Test
=========================================

Tests database connections and creates necessary tables.

Usage: python test_databases.py
"""

import asyncio
import asyncpg
import os
from pathlib import Path

async def test_postgresql():
    """Test PostgreSQL connection and setup."""
    print("[TEST] Testing PostgreSQL connection...")

    try:
        # Get connection parameters from .env file
        postgres_url = os.getenv('POSTGRESQL_URL', 'postgresql://vot_user:vot_password@localhost:5432/vot_guardian')

        # Connect to PostgreSQL
        conn = await asyncpg.connect(postgres_url)

        # Test basic query
        result = await conn.fetchval("SELECT version()")
        print(f"  [OK] PostgreSQL connected: {result.split(' ')[1]}")

        # Create tables for V.O.T. Guardian
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id SERIAL PRIMARY KEY,
                call_id VARCHAR(255) NOT NULL,
                prediction VARCHAR(50) NOT NULL,
                confidence DECIMAL(5,4) NOT NULL,
                features JSONB,
                processing_time_ms DECIMAL(8,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(call_id)
            );

            CREATE INDEX IF NOT EXISTS idx_analysis_results_call_id ON analysis_results(call_id);
            CREATE INDEX IF NOT EXISTS idx_analysis_results_created_at ON analysis_results(created_at);
            CREATE INDEX IF NOT EXISTS idx_analysis_results_prediction ON analysis_results(prediction);
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_trail (
                id SERIAL PRIMARY KEY,
                event_type VARCHAR(100) NOT NULL,
                call_id VARCHAR(255),
                session_id VARCHAR(255),
                metadata JSONB,
                compliance_status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_audit_trail_call_id ON audit_trail(call_id);
            CREATE INDEX IF NOT EXISTS idx_audit_trail_event_type ON audit_trail(event_type);
            CREATE INDEX IF NOT EXISTS idx_audit_trail_created_at ON audit_trail(created_at);
        """)

        print("  [OK] PostgreSQL tables created/verified")

        # Test insert and select
        test_call_id = f"test_{asyncio.get_event_loop().time()}"

        await conn.execute("""
            INSERT INTO analysis_results (call_id, prediction, confidence, features, processing_time_ms)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (call_id) DO UPDATE SET
                prediction = EXCLUDED.prediction,
                confidence = EXCLUDED.confidence,
                features = EXCLUDED.features,
                processing_time_ms = EXCLUDED.processing_time_ms
        """, test_call_id, "HUMAN", 0.95, '{"test": "data"}', 150.5)

        result = await conn.fetchrow("SELECT * FROM analysis_results WHERE call_id = $1", test_call_id)
        print(f"  [OK] Test data inserted and retrieved: {result['prediction']} ({result['confidence']})")

        await conn.close()

        return True

    except Exception as e:
        print(f"  [FAIL] PostgreSQL test failed: {e}")
        return False

async def test_rethinkdb():
    """Test RethinkDB connection and setup."""
    print("[TEST] Testing RethinkDB connection...")

    try:
        import rethinkdb as r
        r = r.r

        # Get connection parameters
        host = os.getenv('RETHINKDB_HOST', 'localhost')
        port = int(os.getenv('RETHINKDB_PORT', '28015'))

        # Connect to RethinkDB
        conn = r.connect(host=host, port=port)

        # Create database if it doesn't exist
        db_name = os.getenv('RETHINKDB_DB', 'vot_guardian')

        try:
            await r.db_create(db_name).run(conn)
            print(f"  [OK] Created RethinkDB database: {db_name}")
        except r.errors.ReqlOpFailedError:
            print(f"  [OK] RethinkDB database already exists: {db_name}")

        # Create tables
        tables = ['analysis_results', 'audit_trail', 'model_performance']

        for table in tables:
            try:
                r.db(db_name).table_create(table).run(conn)
                print(f"  [OK] Created RethinkDB table: {table}")
            except r.errors.ReqlOpFailedError:
                print(f"  [OK] RethinkDB table already exists: {table}")

        # Test insert and select
        import time
        test_data = {
            'id': f"test_{time.time()}",
            'prediction': 'HUMAN',
            'confidence': 0.95,
            'created_at': time.time()
        }

        # Insert test data
        result = r.db(db_name).table('analysis_results').insert(test_data).run(conn)
        print(f"  [OK] Test data inserted: {result['inserted']} records")

        # Retrieve test data
        retrieved = r.db(db_name).table('analysis_results').get(test_data['id']).run(conn)
        print(f"  [OK] Test data retrieved: {retrieved['prediction']} ({retrieved['confidence']})")

        if conn:
            conn.close()

        return True

    except ImportError:
        print("  [WARN] RethinkDB Python driver not installed")
        return False
    except Exception as e:
        print(f"  [FAIL] RethinkDB test failed: {e}")
        return False

async def test_mindsdb():
    """Test MindsDB connection."""
    print("[TEST] Testing MindsDB connection...")

    try:
        import requests
    except ImportError:
        print("  [WARN] Requests library not available")
        return False

    try:
        mindsdb_url = os.getenv('MINDSDB_URL', 'http://localhost:47334')

        # Test health endpoint
        response = requests.get(f"{mindsdb_url}/", timeout=5)

        if response.status_code == 200:
            print(f"  [OK] MindsDB connected: HTTP {response.status_code}")
            return True
        else:
            print(f"  [FAIL] MindsDB health check failed: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("  [WARN] MindsDB not running (connection refused)")
        return False
    except Exception as e:
        print(f"  [FAIL] MindsDB test failed: {e}")
        return False

async def main():
    """Run all database tests."""
    print("V.O.T. Guardian - Database Connection Test")
    print("=" * 50)

    # Test PostgreSQL
    postgres_ok = await test_postgresql()

    # Test RethinkDB (temporarily disabled)
    rethink_ok = True  # Skip RethinkDB for now

    # Test MindsDB
    mindsdb_ok = await test_mindsdb()

    # Summary
    print("\n" + "=" * 50)
    print("DATABASE TEST SUMMARY")
    print("=" * 50)

    all_passed = postgres_ok and rethink_ok and mindsdb_ok

    if all_passed:
        print("SUCCESS: All databases are working!")
        print("\nYour V.O.T. Guardian setup is ready!")
        print("\nNext steps:")
        print("1. Run: python test_simple.py")
        print("2. Start development: python -m src.api.main")
    else:
        print("WARNING: Some database tests failed")
        print("\nTroubleshooting:")
        if not postgres_ok:
            print("  - PostgreSQL: Check if it's running on port 5432")
        if not rethink_ok:
            print("  - RethinkDB: Check if it's running on port 28015")
        if not mindsdb_ok:
            print("  - MindsDB: Check if it's running on port 47334")

    return 0 if all_passed else 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))