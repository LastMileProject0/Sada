"""Regression coverage for outer runner and nested holdout guard composition."""
from pathlib import Path
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / 'scripts/security/run_offline_backend.py'


def test_nested_guard_rejects_before_dns_and_outer_guard_still_denies():
    guard = runpy.run_path(str(RUNNER))['GUARD']
    program = guard + """
from analysis.grounding_holdout.offline import OfflineViolation, forbid_network
from urllib import request

def unexpected_io(*args, **kwargs):
    raise AssertionError('Native external I/O must never be attempted')

_resolve = _connect = _connect_ex = unexpected_io
for attempt in (
    lambda: socket.getaddrinfo('guard-check.invalid', 443),
    lambda: request.urlopen('https://guard-check.invalid'),
):
    try:
        with forbid_network():
            attempt()
    except OfflineViolation:
        pass
    else:
        raise AssertionError('Inner guard must reject before outer DNS wrapper')

# Once the nested guard exits, the outer guard must remain active.
for attempt in (
    lambda: socket.getaddrinfo('guard-check.invalid', 443),
    lambda: socket.socket().connect(('203.0.113.1', 443)),
    lambda: socket.socket().connect_ex(('203.0.113.1', 443)),
):
    try:
        attempt()
    except OSError:
        pass
    else:
        raise AssertionError('Outer guard must deny external I/O')
"""
    result = subprocess.run([sys.executable, '-c', program], cwd=ROOT / 'backend',
                            capture_output=True, timeout=10)
    assert result.returncode == 0


def test_runner_removes_temporary_database_and_model_credentials(monkeypatch):
    namespace = runpy.run_path(str(RUNNER))
    keys = ['OPENROUTER_API_KEY', 'NEON_SETUP_ADMIN_DSN', 'SADA_APP_DB_PASSWORD',
            'SADA_POSTGRES_DSN', 'SADA_DEV_POSTGRES_DSN', 'DATABASE_URL',
            'PGHOST', 'PGPORT', 'PGUSER', 'PGPASSWORD', 'PGDATABASE']
    for key in keys:
        monkeypatch.setenv(key, 'offline-test-placeholder')
    observed = {}

    def child(_args, **kwargs):
        observed['keys'] = set(kwargs['env'])
        observed['backend'] = kwargs['env']['SADA_STORAGE_BACKEND']
        observed['path'] = kwargs['env']['SADA_EVAL_DB']
        return type('Result', (), {'returncode': 0})()

    monkeypatch.setattr(subprocess, 'run', child)
    assert namespace['main']() == 0
    assert not (set(keys) & observed['keys'])
    assert observed['backend'] == 'sqlite'
    assert Path(observed['path']).name == 'isolated.sqlite'
