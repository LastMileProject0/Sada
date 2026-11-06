"""Ownership and lossless, repeatable backed-up migration regression tests."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
import sqlite3
from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest
from sada_bridge.api import create_app
from sada_bridge.migrations import ensure_ownership_schema
from sada_bridge.storage import EvaluationStore

SAMPLE = {'scenario': 'AL_WADI_FLASH_FLOOD', 'stage': 'T+04',
          'enabledChannelIds': ['CH01', 'CH02', 'CH03', 'CH04', 'CH05']}
A, B = 'a' * 64, 'b' * 64


def legacy_database(path):
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE evaluation_results (id TEXT PRIMARY KEY, '
                     'result TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
        conn.execute('INSERT INTO evaluation_results (id, result) VALUES (?, ?)',
                     ('00000000-0000-4000-8000-000000000001', '{"legacy":"preserved"}'))


def test_migration_backs_up_before_change_and_preserves_exact_rows(tmp_path):
    path = tmp_path / 'legacy.sqlite'
    legacy_database(path)
    report = ensure_ownership_schema(path)
    assert report['migrated'] and report['preserved_rows'] == 1
    backup = report['backup']
    assert os.stat(backup).st_mode & 0o777 == 0o600
    with sqlite3.connect(backup) as before, sqlite3.connect(path) as after:
        assert before.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert 'owner_session_hash' not in {r[1] for r in before.execute(
            'PRAGMA table_info(evaluation_results)')}
        query = 'SELECT id, result, created_at FROM evaluation_results'
        assert before.execute(query).fetchall() == after.execute(query).fetchall()
        assert after.execute('SELECT owner_session_hash FROM evaluation_results').fetchone() == (None,)
    assert ensure_ownership_schema(path)['migrated'] is False
    assert len(list((tmp_path / 'backups').glob('*.sqlite3'))) == 1


def test_concurrent_migration_is_repeatable(tmp_path):
    path = tmp_path / 'legacy.sqlite'
    legacy_database(path)
    with ThreadPoolExecutor(max_workers=3) as pool:
        reports = list(pool.map(ensure_ownership_schema, [path] * 3))
    assert sum(r['migrated'] for r in reports) == 1
    assert len(list((tmp_path / 'backups').glob('*.sqlite3'))) == 1


def test_backup_failure_does_not_apply_schema_change(tmp_path):
    path = tmp_path / 'legacy.sqlite'
    legacy_database(path)
    with patch('sada_bridge.migrations.os.open', side_effect=OSError('backup refused')):
        with pytest.raises(OSError):
            ensure_ownership_schema(path)
    with sqlite3.connect(path) as conn:
        assert 'owner_session_hash' not in {r[1] for r in conn.execute(
            'PRAGMA table_info(evaluation_results)')}
        assert conn.execute('SELECT COUNT(*) FROM evaluation_results').fetchone()[0] == 1


def test_two_owners_are_isolated_and_no_owner_is_leaked(tmp_path):
    path = tmp_path / 'owned.sqlite'
    with TestClient(create_app(path)) as client:
        ids = []
        for owner in [A, B]:
            response = client.post('/api/evaluations', json=SAMPLE,
                                   headers={'X-SADA-Owner': owner})
            assert response.status_code == 201
            ids.append(response.json()['id'])
        for owner, ident, other in [(A, ids[0], ids[1]), (B, ids[1], ids[0])]:
            allowed = client.get(f'/api/evaluations/{ident}', headers={'X-SADA-Owner': owner})
            assert allowed.status_code == 200
            assert owner not in json.dumps(allowed.json())
            denied = client.get(f'/api/evaluations/{other}', headers={'X-SADA-Owner': owner})
            missing = client.get('/api/evaluations/00000000-0000-4000-8000-000000000000',
                                 headers={'X-SADA-Owner': owner})
            assert denied.status_code == missing.status_code == 404
            assert denied.json() == missing.json() == {'detail': 'Evaluation not found'}
        for owner in [None, '', 'invalid', 'c' * 64]:
            headers = {'X-SADA-Owner': owner} if owner is not None else {}
            denied = client.get(f'/api/evaluations/{ids[0]}', headers=headers)
            assert denied.status_code == 404
        assert client.post('/api/evaluations', json=SAMPLE).status_code == 404
    with TestClient(create_app(path)) as restarted:
        assert restarted.get(f'/api/evaluations/{ids[0]}',
                             headers={'X-SADA-Owner': A}).status_code == 200


def test_legacy_is_never_claimed_or_deleted(tmp_path):
    path = tmp_path / 'legacy.sqlite'
    legacy_database(path)
    with TestClient(create_app(path)) as client:
        for owner in [A, B]:
            response = client.get('/api/evaluations/00000000-0000-4000-8000-000000000001',
                                  headers={'X-SADA-Owner': owner})
            assert response.status_code == 404
    store = EvaluationStore(path)
    assert store.load('00000000-0000-4000-8000-000000000001', A) is None
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT result, owner_session_hash FROM evaluation_results').fetchall() == [
            ('{"legacy":"preserved"}', None)]
