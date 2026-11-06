"""Fail-closed production preflight, no DB connection or published service.

The former SQLite production smoke is intentionally retired: production can no
longer run on ephemeral SQLite. Positive PG/supervisor smoke needs a separately
approved real PostgreSQL instance and runtime role.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    with tempfile.TemporaryDirectory(prefix='sada-production-negative-') as folder:
        path = Path(folder) / 'must-not-create.sqlite'
        base = {**os.environ, 'NODE_ENV': 'production',
                'SESSION_SECRET': 'isolated-production-test-signing-key-only',
                'SADA_PUBLIC_ORIGIN': 'https://sada-smoke-test.invalid',
                'SADA_EVAL_DB': str(path), 'SADA_POSTGRES_DSN': ''}
        for backend in ['', 'sqlite', 'postgres', 'unsupported']:
            result = subprocess.run(
                [sys.executable, 'scripts/production/run.py'], cwd=ROOT,
                env={**base, 'SADA_STORAGE_BACKEND': backend},
                capture_output=True, timeout=10,
            )
            assert result.returncode == 1 and not path.exists()
            assert b'Production startup failed:' in result.stderr
    print('PASS: production refuses missing/SQLite/unsupported/unconfigured storage; '
          'no database created, no database connection attempted.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
