"""Offline transaction/authorization contracts. NOT real PostgreSQL verification."""
import copy
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from sada_bridge.api import create_app
from sada_bridge.postgres import PostgresEvaluationStore
from sada_bridge.postgres_schema import CAPACITY_LOCK, EXECUTION_LOCK, check_schema, validate_row
from sada_bridge.storage import (
    EvaluationStore, EvaluationBusy, StorageCapacityReached, StorageUnavailable,
    MAX_RESULTS, MAX_TOTAL_BYTES, MAX_RESULT_BYTES,
)
from sada_bridge.storage_backend import create_store
from sada_bridge.storage_transfer import fingerprint, import_snapshot, read_snapshot

DSN = 'postgresql://test:never-real@db.invalid/sada?sslmode=verify-full'
A, B = 'a' * 64, 'b' * 64
ID = str(UUID(int=1))
STAMP = '2026-11-03 01:02:03'


class Cursor:
    def __init__(self, rows=()):
        self.rows = list(rows)
    def fetchone(self):
        return self.rows[0] if self.rows else None
    def fetchall(self):
        return self.rows


class FakeDB:
    """Deliberately small SQL/transaction spy, not a PG parser or emulator."""
    def __init__(self):
        self.rows, self.locks, self.calls = {}, set(), []
        self.connections = 0
        self.schema_ok = True
        self.privileges = (True, False, False, False)
    def connect(self, *args, **kwargs):
        self.connections += 1
        return FakeConnection(self)


class FakeConnection:
    def __init__(self, db):
        self.db, self.rows, self.held = db, copy.deepcopy(db.rows), set()
    def __enter__(self):
        return self
    def __exit__(self, kind, value, tb):
        if kind is None:
            self.db.rows = self.rows
        self.db.locks.difference_update(self.held)
    def execute(self, sql, params=None, **kwargs):
        self.db.calls.append((sql, params))
        if 'pg_try_advisory_xact_lock' in sql:
            key = params[0]
            ok = key not in self.db.locks or key in self.held
            if ok:
                self.db.locks.add(key)
                self.held.add(key)
            return Cursor([(ok,)])
        if 'pg_attribute' in sql:
            return Cursor([('id', 'text', True), ('result', 'text', True),
                           ('created_at', 'text', True), ('owner_session_hash', 'text', False)]
                          if self.db.schema_ok else [])
        if 'pg_constraint' in sql:
            return Cursor([
                ('evaluation_results_pkey', 'p', 'PRIMARY KEY (id)'),
                ('evaluation_results_result_bytes', 'c', 'CHECK ((octet_length(result) <= 262144))'),
                ('evaluation_results_result_object', 'c', "CHECK ((jsonb_typeof((result)::jsonb) = 'object'::text))"),
                ('evaluation_results_owner_format', 'c', "CHECK ((owner_session_hash ~ '^[0-9a-f]{64}$'::text))"),
            ])
        if 'pg_index' in sql:
            return Cursor([('owner_session_hash', 'id', '(owner_session_hash IS NOT NULL)')])
        if 'has_table_privilege' in sql:
            return Cursor([self.db.privileges])
        if sql.startswith('SELECT COUNT(*)'):
            return Cursor([(len(self.rows), sum(len(r[1].encode('utf-8')) for r in self.rows.values()))])
        if sql.startswith('INSERT INTO'):
            assert params[0] not in self.rows
            self.rows[params[0]] = tuple(params)
            return Cursor()
        if sql.startswith('SELECT result FROM'):
            row = self.rows.get(params[0])
            return Cursor([(row[1],)] if row and row[3] is not None and row[3] == params[1] else [])
        if sql.startswith('SELECT id, result, created_at, owner_session_hash FROM') and params:
            row = self.rows.get(params[0])
            return Cursor([row] if row else [])
        if sql.startswith('SELECT id, result, created_at, owner_session_hash FROM') and 'LIMIT 0' in sql:
            return Cursor()
        if sql.startswith('SET TRANSACTION') or 'CREATE TABLE IF NOT EXISTS' in sql:
            return Cursor()
        raise AssertionError('Unexpected SQL in offline spy')


@pytest.fixture
def pg(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr('sada_bridge.postgres.psycopg.connect', db.connect)
    return PostgresEvaluationStore(DSN, production=True), db


def row(i=1, owner=A):
    identifier = str(UUID(int=i))
    return (identifier, json.dumps({'id': identifier, 'note': 'نص عربي'}, ensure_ascii=False),
            STAMP, owner)


def test_storage_selector_keeps_sqlite_explicit_and_ignores_managed_url(tmp_path):
    path = tmp_path / 'local.sqlite'
    store = create_store(environ={'DATABASE_URL': DSN, 'SADA_EVAL_DB': str(path)})
    assert isinstance(store, EvaluationStore)
    assert isinstance(create_store(environ={'SADA_STORAGE_BACKEND': 'postgres',
                                          'SADA_POSTGRES_DSN': DSN}), PostgresEvaluationStore)


@pytest.mark.parametrize('env', [
    {}, {'SADA_STORAGE_BACKEND': 'sqlite'}, {'SADA_STORAGE_BACKEND': 'postgres'},
    {'SADA_STORAGE_BACKEND': 'unknown'},
    {'SADA_STORAGE_BACKEND': 'postgres', 'SADA_POSTGRES_DSN': DSN.replace('verify-full', 'disable')},
    {'SADA_STORAGE_BACKEND': 'postgres', 'SADA_POSTGRES_DSN': 'invalid'},
])
def test_production_config_fails_without_explicit_valid_durable_store(tmp_path, env):
    with pytest.raises(StorageUnavailable) as caught:
        create_store(environ={**env, 'SADA_EVAL_DB': str(tmp_path / 'no.sqlite')}, production=True)
    assert 'never-real' not in str(caught.value)
    assert not (tmp_path / 'no.sqlite').exists()


def test_save_load_session_and_legacy_isolation(pg):
    store, db = pg
    result = json.loads(row()[1])
    with store.execution_slot():
        store.save(result, A)
    assert store.load(ID, A) == result
    assert store.load(ID, B) is None
    db.rows[str(UUID(int=2))] = row(2, None)
    assert store.load(str(UUID(int=2)), A) is None
    assert store.load(str(UUID(int=3)), A) is None
    before = db.connections
    assert store.load(ID, None) is None and store.load(ID, 'tampered') is None
    assert db.connections == before
    queries = [s for s, p in db.calls if s.startswith('SELECT result FROM')]
    assert all('WHERE id = %s AND owner_session_hash = %s' in q for q in queries)
    assert all('never-real' not in s and A not in s for s, p in db.calls)


@pytest.mark.parametrize('key', [EXECUTION_LOCK, CAPACITY_LOCK])
def test_nonwaiting_lock_denial_is_bounded_and_does_not_insert(pg, key):
    store, db = pg
    db.locks.add(key)
    with pytest.raises(EvaluationBusy):
        with store.execution_slot():
            store.save(json.loads(row()[1]), A)
    assert not db.rows


def test_execution_and_save_share_one_transaction_and_release_on_failure(pg):
    store, db = pg
    with pytest.raises(ValueError):
        with store.execution_slot():
            store.save(json.loads(row()[1]), A)
            raise ValueError('simulate downstream failure')
    assert db.connections == 1 and not db.rows and not db.locks
    with store.execution_slot():
        store.save(json.loads(row()[1]), A)
    assert len(db.rows) == 1 and not db.locks


def test_row_count_limit_preserves_existing_results(pg):
    store, db = pg
    db.rows = {str(UUID(int=i)): row(i) for i in range(1, MAX_RESULTS + 1)}
    with pytest.raises(StorageCapacityReached):
        with store.execution_slot():
            pass
    assert len(db.rows) == MAX_RESULTS and store.load(ID, A)


def test_last_allowed_row_and_result_size(pg):
    store, db = pg
    db.rows = {str(UUID(int=i)): row(i) for i in range(2, MAX_RESULTS + 1)}
    store.save(json.loads(row()[1]), A)
    assert len(db.rows) == MAX_RESULTS
    with pytest.raises(StorageCapacityReached):
        store.save({'id': str(UUID(int=999)), 'padding': 'x' * MAX_RESULT_BYTES}, A)
    assert len(db.rows) == MAX_RESULTS


def test_aggregate_byte_limit_uses_utf8_bytes_and_no_eviction(pg, monkeypatch):
    store, db = pg
    monkeypatch.setattr('sada_bridge.postgres.MAX_TOTAL_BYTES', len(row()[1].encode('utf-8')))
    with pytest.raises(StorageCapacityReached):
        store.save(json.loads(row()[1]), A)
    assert not db.rows


def test_schema_readiness_is_read_only_and_validates_grants(pg):
    store, db = pg
    store.check_readable()
    assert not any('CREATE' in s or 'INSERT INTO' in s or 'ALTER' in s for s, p in db.calls)
    db.privileges = (True, True, True, True)
    with pytest.raises(StorageUnavailable):
        store.check_readable()
    db.schema_ok = False
    with pytest.raises(StorageUnavailable):
        store.check_readable()


def test_driver_errors_never_include_dsn_or_fallback_to_sqlite(monkeypatch, tmp_path):
    def unavailable(*args, **kwargs):
        raise OSError(DSN)
    monkeypatch.setattr('sada_bridge.postgres.psycopg.connect', unavailable)
    store = PostgresEvaluationStore(DSN)
    for operation in [store.check_readable, lambda: store.load(ID, A),
                      lambda: store.save(json.loads(row()[1]), A)]:
        with pytest.raises(StorageUnavailable) as caught:
            operation()
        assert DSN not in str(caught.value) and 'never-real' not in str(caught.value)


def snapshot_file(path, rows, legacy=False):
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE evaluation_results (id TEXT PRIMARY KEY, result TEXT, created_at TEXT' +
                     (')' if legacy else ', owner_session_hash TEXT)'))
        for r in rows:
            conn.execute('INSERT INTO evaluation_results VALUES (' +
                         (','.join('?' for _ in r[:3]) if legacy else '?,?,?,?') + ')',
                         r[:3] if legacy else r)
    return path


@pytest.mark.parametrize('legacy', [True, False])
def test_read_only_snapshot_preserves_json_timestamp_uuid_and_null(tmp_path, legacy):
    path = snapshot_file(tmp_path / 'backup.sqlite', [row(1, None), row(2, A)], legacy)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    rows = read_snapshot(path)
    assert rows[0] == row(1, None)
    assert rows[1] == row(2, None if legacy else A)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_repeat_import_is_exact_no_overwrite_and_conflict_rolls_back(pg):
    store, db = pg
    rows = [row(1, None), row(2, A)]
    first = import_snapshot(store, rows)
    assert first['inserted'] == 2 and db.rows[ID][3] is None
    second = import_snapshot(store, rows)
    assert second['inserted'] == 0 and second['field_fingerprint'] == fingerprint(rows)
    baseline = copy.deepcopy(db.rows)
    with pytest.raises(ValueError):
        import_snapshot(store, [row(3, B), (*row(2, A)[:2], '2026-11-04 00:00:00', A)])
    assert db.rows == baseline


@pytest.mark.parametrize('bad', [
    ('not-a-uuid', '{}', STAMP, None),
    (ID, '[]', STAMP, None),
    (ID, '{"id":"different"}', STAMP, A),
    (ID, json.dumps({'id': ID}), 'invalid-date', A),
    (ID, json.dumps({'id': ID}), STAMP, 'A' * 64),
    (ID, '{"id":"' + ID + '","bad":NaN}', STAMP, None),
])
def test_invalid_snapshot_aborts_before_target_connection(pg, bad):
    store, db = pg
    with pytest.raises((ValueError, StorageCapacityReached)):
        import_snapshot(store, [bad])
    assert db.connections == 0


class DownStore:
    def check_readable(self):
        raise StorageUnavailable(DSN)
    def load(self, *args):
        raise StorageUnavailable(DSN)
    @contextmanager
    def execution_slot(self):
        raise StorageUnavailable(DSN)
        yield


def test_api_outages_are_generic_and_unauthorized_still_uniform_404():
    with TestClient(create_app(storage=DownStore())) as client:
        assert client.get('/api/health').status_code == 503
        denied = client.get('/api/evaluations/' + ID)
        assert denied.status_code == 404
        response = client.get('/api/evaluations/' + ID, headers={'X-SADA-Owner': A})
        assert response.status_code == 503 and response.json() == {'detail': 'Evaluation storage unavailable'}
        assert 'never-real' not in response.text
        body = {'scenario': 'AL_WADI_FLASH_FLOOD', 'stage': 'T+04',
                'enabledChannelIds': ['CH01', 'CH02', 'CH03', 'CH04', 'CH05']}
        failed = client.post('/api/evaluations', json=body, headers={'X-SADA-Owner': A})
        assert failed.status_code == 503 and failed.json() == response.json()


def load_script(relative):
    path = Path(__file__).parents[2] / relative
    spec = importlib.util.spec_from_file_location('isolated_preparation_script', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_development_schema_is_repeatable_and_never_runs_at_startup(pg):
    store, db = pg
    script = load_script('scripts/storage/prepare_postgres.py')
    script.apply_development_schema(store)
    script.apply_development_schema(store)
    assert not db.rows
    assert len([s for s, p in db.calls if 'CREATE TABLE IF NOT EXISTS' in s]) == 2
    db.schema_ok = False
    with pytest.raises(StorageUnavailable):
        script.apply_development_schema(store)


def test_cli_defaults_to_readonly_and_refuses_unapproved_or_production(tmp_path, monkeypatch, capsys):
    script = load_script('scripts/storage/prepare_postgres.py')
    path = snapshot_file(tmp_path / 'backup.sqlite', [row(1, None)])
    monkeypatch.setenv('NODE_ENV', 'development')
    assert script.main(['--source-backup', str(path)]) == 0
    assert json.loads(capsys.readouterr().out)['mode'] == 'read-only-backup-validation'
    assert script.main(['--apply-development-schema']) == 1
    monkeypatch.setenv('NODE_ENV', 'production')
    assert script.main(['--apply-development-schema', '--confirm-development-target']) == 1


def test_supervisor_requires_pg_readiness_before_children(tmp_path, monkeypatch, pg):
    store, db = pg
    script = load_script('scripts/production/run.py')
    monkeypatch.setattr(script, 'ROOT', tmp_path)
    for relative in ['artifacts/api-server/dist/index.mjs', 'artifacts/sada/dist/public/index.html']:
        p = tmp_path / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('isolated build fixture')
    monkeypatch.setenv('SESSION_SECRET', 'isolated-runtime-signing-key-32-bytes')
    monkeypatch.setenv('SADA_PUBLIC_ORIGIN', 'https://isolated.invalid')
    monkeypatch.delenv('PORT', raising=False)
    monkeypatch.delenv('SADA_PYTHON_PORT', raising=False)
    monkeypatch.setattr('sada_bridge.storage_backend.create_store', lambda **kw: store)
    assert script.require_configuration() == [8080, 8000]
    db.schema_ok = False
    with pytest.raises(StorageUnavailable):
        script.require_configuration()
