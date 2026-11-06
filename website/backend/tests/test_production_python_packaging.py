"""Packaging configuration and safe diagnostics, without network/DB access."""
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def supervisor():
    spec = importlib.util.spec_from_file_location(
        'python_packaging_test', ROOT / 'scripts/production/run.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dependencies_ship_but_are_not_committed():
    deploy_rules = (ROOT / '.replitignore').read_text().splitlines()
    git_rules = (ROOT / '.gitignore').read_text().splitlines()
    assert '.pythonlibs/' in git_rules
    assert not any(rule.strip() in {'.pythonlibs', '.pythonlibs/', '/.pythonlibs',
                                   '/.pythonlibs/'} for rule in deploy_rules)
    # Existing private-data and credential exclusions must not be relaxed.
    for rule in ['**/.sada_api/', '.env', '.env.*', '.neon', '/generated-artifacts/']:
        assert rule in deploy_rules


def test_runtime_prepares_exact_payload_path(supervisor, monkeypatch, tmp_path):
    monkeypatch.setattr(supervisor, 'ROOT', tmp_path)
    monkeypatch.setattr(sys, 'path', list(sys.path))
    packages = (tmp_path / '.pythonlibs/lib'
                / f'python{sys.version_info.major}.{sys.version_info.minor}/site-packages')
    packages.mkdir(parents=True)
    monkeypatch.setenv('PYTHONPATH', '/development-only-test-path')
    env = supervisor.prepare_python_runtime()
    assert sys.path[0] == str(packages)
    assert env == {'PYTHONPATH': str(packages)}
    assert '/development-only-test-path' not in env['PYTHONPATH']


def test_missing_payload_fails_closed(supervisor, monkeypatch, tmp_path):
    monkeypatch.setattr(supervisor, 'ROOT', tmp_path)
    with pytest.raises(RuntimeError, match='Packaged Python runtime dependencies are missing'):
        supervisor.prepare_python_runtime()


def test_missing_module_diagnostics_do_not_print_exception_messages(supervisor):
    marker = 'synthetic-sensitive-message-not-for-logs'
    error = ModuleNotFoundError(marker, name='psycopg')
    assert supervisor.safe_startup_error(error) == 'ModuleNotFoundError: psycopg'
    for name in [None, 'postgresql://synthetic-credential.invalid', '/private/source/path',
                 'bad name', '']:
        result = supervisor.safe_startup_error(ModuleNotFoundError(marker, name=name))
        assert result == 'ModuleNotFoundError'
        assert marker not in result
    assert supervisor.safe_startup_error(ValueError(marker)) == 'ValueError'
