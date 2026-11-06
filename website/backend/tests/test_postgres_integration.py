"""Real PG17 tests against a NEW disposable LOCAL Unix-socket cluster ONLY.

No network DB, existing DATABASE_URL, SQLite data or AI endpoint is used.
Tests skip if local binaries are unavailable. Nothing persists after teardown.
"""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from uuid import uuid4

import psycopg
import pytest

from sada_bridge.postgres import PostgresEvaluationStore
from sada_bridge.storage import EvaluationBusy, StorageCapacityReached, StorageUnavailable, MAX_RESULTS
from sada_bridge.storage_transfer import import_snapshot, read_snapshot

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def cluster():
    if not all(shutil.which(p) for p in ['initdb', 'pg_ctl']) or os.geteuid() == 0:
        pytest.skip('Disposable local PostgreSQL binaries/non-root user required')
    with tempfile.TemporaryDirectory(prefix='sada-local-pg-') as temp:
        base = Path(temp)
        data, sockets = base / 'data', base / 'socket'
        sockets.mkdir(mode=0o700)
        subprocess.run(['initdb', '-D', str(data), '-U', 'sada_test_admin',
                        '--auth-local=trust', '--auth-host=reject', '--no-locale', '-E', 'UTF8'],
                       check=True, capture_output=True)
        subprocess.run(['pg_ctl', '-D', str(data), '-l', str(base / 'postgres.log'),
                        '-o', f"-c listen_addresses='' -k {sockets} -c fsync=off", '-w', 'start'],
                       check=True, capture_output=True)
        admin_dsn = f'host={sockets} dbname=postgres user=sada_test_admin sslmode=verify-full'
        runtime_dsn = f'host={sockets} dbname=postgres user=sada_test_runtime sslmode=verify-full'
        try:
            with psycopg.connect(admin_dsn) as conn:
                conn.execute((ROOT / 'backend/sada_bridge/postgres_schema.sql').read_text(), prepare=False)
                conn.execute('CREATE ROLE sada_test_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE')
                conn.execute('REVOKE ALL ON public.evaluation_results FROM PUBLIC')
                conn.execute('GRANT USAGE ON SCHEMA public TO sada_test_runtime')
                conn.execute('GRANT SELECT, INSERT ON public.evaluation_results TO sada_test_runtime')
            yield admin_dsn, runtime_dsn
        finally:
            subprocess.run(['pg_ctl', '-D', str(data), '-m', 'immediate', '-w', 'stop'],
                           check=True, capture_output=True)


@pytest.fixture
def real_pg(cluster):
    admin, runtime = cluster
    with psycopg.connect(admin) as conn:
        conn.execute('TRUNCATE public.evaluation_results')  # Disposable synthetic table ONLY.
    return PostgresEvaluationStore(runtime, production=True), PostgresEvaluationStore(admin)


def fixture_row(owner=None):
    identifier = str(uuid4())
    raw = json.dumps({'id': identifier, 'note': 'اختبار synthetic'}, ensure_ascii=False)
    return identifier, raw, '2026-11-03 01:02:03', owner


def test_real_schema_repeatability_permissions_and_no_runtime_ddl(real_pg):
    store, admin = real_pg
    sql = (ROOT / 'backend/sada_bridge/postgres_schema.sql').read_text()
    for _ in range(2):
        with admin.connection() as conn:
            conn.execute(sql, prepare=False)
        store.check_readable()
    with pytest.raises(StorageUnavailable):
        PostgresEvaluationStore(admin._dsn, production=True).check_readable()
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with psycopg.connect(store._dsn) as conn:
            conn.execute('DELETE FROM public.evaluation_results')


def test_disposable_dump_restore_preserves_ownership_and_raw_fields(real_pg, tmp_path):
    """Backup/restore rehearsal ONLY in this test's new local socket cluster."""
    store, admin = real_pg
    rows = sorted([fixture_row(), fixture_row('a' * 64), fixture_row('b' * 64)])
    with admin.connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany('INSERT INTO public.evaluation_results VALUES (%s,%s,%s,%s)', rows)
    archive = tmp_path / 'synthetic-only.dump'
    options = psycopg.conninfo.conninfo_to_dict(admin._dsn)
    assert options['host'].startswith('/tmp/')  # Never an inherited network DB.
    env = {**os.environ, 'PGHOST': options['host'], 'PGUSER': options['user'],
           'PGDATABASE': 'postgres', 'PGCONNECT_TIMEOUT': '3'}
    for key in ['PGPASSWORD', 'PGSERVICE', 'PGSERVICEFILE']:
        env.pop(key, None)
    subprocess.run(['pg_dump', '--format=custom', '--table=public.evaluation_results',
                    '--file', str(archive)], env=env, check=True, capture_output=True)
    archive.chmod(0o600)
    assert archive.stat().st_mode & 0o777 == 0o600
    # Dedicated restore DB, never the source or any existing application DB.
    with psycopg.connect(admin._dsn, autocommit=True) as conn:
        conn.execute('CREATE DATABASE sada_disposable_restore')
    subprocess.run(['pg_restore', '--exit-on-error', '--dbname=sada_disposable_restore',
                    str(archive)], env=env, check=True, capture_output=True)
    restored_dsn = psycopg.conninfo.make_conninfo(admin._dsn, dbname='sada_disposable_restore')
    with psycopg.connect(restored_dsn) as conn:
        assert conn.execute('SELECT id,result,created_at,owner_session_hash '
                            'FROM public.evaluation_results ORDER BY id').fetchall() == rows
    restored_runtime = PostgresEvaluationStore(
        psycopg.conninfo.make_conninfo(store._dsn, dbname='sada_disposable_restore'),
        production=True)
    restored_runtime.check_readable()
    for row in rows:
        assert restored_runtime.load(row[0], 'c' * 64) is None
        assert restored_runtime.load(row[0], 'a' * 64) == (
            json.loads(row[1]) if row[3] == 'a' * 64 else None)
        assert restored_runtime.load(row[0], 'b' * 64) == (
            json.loads(row[1]) if row[3] == 'b' * 64 else None)
    # Both databases/archive disappear with their temporary fixtures.


def test_real_atomic_import_preserves_raw_fields_null_and_conflicts(real_pg, tmp_path):
    store, admin = real_pg
    rows = sorted([fixture_row(), fixture_row('a' * 64)])
    path = tmp_path / 'synthetic-backup.sqlite'
    with closing(sqlite3.connect(path)) as conn:
        conn.execute('CREATE TABLE evaluation_results '
                     '(id TEXT PRIMARY KEY, result TEXT, created_at TEXT, owner_session_hash TEXT)')
        conn.executemany('INSERT INTO evaluation_results VALUES (?,?,?,?)', rows)
        conn.commit()
    read = read_snapshot(path)
    assert read == rows
    assert import_snapshot(admin, read)['inserted'] == 2
    assert import_snapshot(admin, read)['inserted'] == 0
    for r in read:
        assert store.load(r[0], 'b' * 64) is None
        assert store.load(r[0], 'a' * 64) == (json.loads(r[1]) if r[3] else None)
    extra = fixture_row('b' * 64)
    conflict = (*rows[0][:3], 'c' * 64)
    with pytest.raises(ValueError):
        import_snapshot(admin, [extra, conflict])
    assert store.load(extra[0], 'b' * 64) is None
    with admin.connection() as conn:
        assert conn.execute('SELECT id,result,created_at,owner_session_hash '
                            'FROM public.evaluation_results ORDER BY id').fetchall() == rows


def test_real_shared_execution_capacity_lock_and_rollback(real_pg):
    first, admin = real_pg
    second = PostgresEvaluationStore(first._dsn, production=True)
    with first.execution_slot():
        with pytest.raises(EvaluationBusy):
            with second.execution_slot():
                pytest.fail('Must not acquire another execution slot')
    data = json.loads(fixture_row('a' * 64)[1])
    with pytest.raises(ValueError):
        with first.execution_slot():
            first.save(data, 'a' * 64)
            raise ValueError('synthetic rollback')
    assert first.load(data['id'], 'a' * 64) is None
    with first.execution_slot():
        first.save(data, 'a' * 64)
    assert first.load(data['id'], 'a' * 64) == data
    rows = [fixture_row('a' * 64) for _ in range(MAX_RESULTS - 1)]
    import_snapshot(admin, rows)
    with pytest.raises(StorageCapacityReached):
        with first.execution_slot():
            pytest.fail('Capacity must fail without deleting prior results')
    assert first.load(data['id'], 'a' * 64) == data


def test_real_capacity_race_cannot_exceed_500_rows(real_pg):
    store, admin = real_pg
    import_snapshot(admin, [fixture_row('a' * 64) for _ in range(MAX_RESULTS - 1)])
    barrier = threading.Barrier(2)
    def save():
        data = json.loads(fixture_row('a' * 64)[1])
        barrier.wait(timeout=5)
        try:
            store.save(data, 'a' * 64)
            return 'saved'
        except (EvaluationBusy, StorageCapacityReached):
            return 'bounded'
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(save) for _ in range(2)]
        outcomes = [f.result(timeout=10) for f in futures]
    assert sorted(outcomes) == ['bounded', 'saved']
    with admin.connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM public.evaluation_results').fetchone()[0] == MAX_RESULTS


@pytest.mark.parametrize('raw,owner', [('[]', None), ('broken', None), ('{}', 'A' * 64),
                                       (json.dumps({'padding': 'x' * 262145}), None)])
def test_real_database_constraints_reject_invalid_rows(real_pg, raw, owner):
    _, admin = real_pg
    with pytest.raises(psycopg.Error):
        with psycopg.connect(admin._dsn) as conn:
            conn.execute('INSERT INTO public.evaluation_results '
                         '(id,result,created_at,owner_session_hash) VALUES (%s,%s,%s,%s)',
                         (str(uuid4()), raw, '2026-11-03 01:02:03', owner))


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def test_real_production_supervisor_two_anonymous_sessions_and_restart(real_pg, cluster):
    store, admin = real_pg
    if not (ROOT / 'artifacts/api-server/dist/index.mjs').exists():
        pytest.skip('Production API build required')
    port, python_port = free_port(), free_port()
    while port == python_port:
        python_port = free_port()
    origin = 'https://isolated-sada-test.invalid'
    env = {**os.environ, 'NODE_ENV': 'production', 'SADA_STORAGE_BACKEND': 'postgres',
           'SADA_POSTGRES_DSN': store._dsn, 'SESSION_SECRET': 'test-only-isolated-signing-key-32-bytes',
           'SADA_PUBLIC_ORIGIN': origin, 'PORT': str(port), 'SADA_PYTHON_PORT': str(python_port)}

    def request(path, method='GET', body=None, cookie=None):
        with closing(http.client.HTTPConnection('127.0.0.1', port, timeout=15)) as conn:
            headers = {'Origin': origin, 'Content-Type': 'application/json'}
            if cookie:
                headers['Cookie'] = cookie
            conn.request(method, path, json.dumps(body) if body else None, headers)
            response = conn.getresponse()
            return response.status, json.loads(response.read()), response.getheader('Set-Cookie')

    def launch(output):
        proc = subprocess.Popen([sys.executable, 'scripts/production/run.py'],
                                cwd=ROOT, env=env, stdout=output, stderr=output)
        for _ in range(150):
            assert proc.poll() is None, 'Production supervisor stopped before readiness'
            try:
                if request('/api/healthz')[0] == 200:
                    return proc
            except (OSError, ValueError):
                pass
            time.sleep(.1)
        proc.terminate()
        proc.wait(timeout=15)
        pytest.fail('Production readiness timed out')

    with tempfile.TemporaryFile() as output:
        process = launch(output)
        try:
            body = {'scenario': 'AL_WADI_FLASH_FLOOD', 'stage': 'T+04',
                    'enabledChannelIds': ['CH01', 'CH02', 'CH03', 'CH04', 'CH05']}
            status, a, issued = request('/api/evaluations', 'POST', body)
            assert status == 201
            assert all(flag in issued for flag in ['Secure', 'HttpOnly', 'SameSite=Lax'])
            cookie_a = issued.split(';')[0]
            status, b, issued = request('/api/evaluations', 'POST', body)
            assert status == 201 and a['id'] != b['id']
            cookie_b = issued.split(';')[0]
            a_path = '/api/evaluations/' + a['id']
            assert request(a_path, cookie=cookie_a)[0] == 200
            assert request(a_path, cookie=cookie_b)[0] == 404
            assert request(a_path)[0] == 404
            legacy = fixture_row()
            import_snapshot(admin, [legacy])
            assert request('/api/evaluations/' + legacy[0], cookie=cookie_a)[0] == 404
            process.terminate()
            process.wait(timeout=15)
            process = launch(output)
            assert request(a_path, cookie=cookie_a)[0] == 200
            assert request(a_path, cookie=cookie_b)[0] == 404
        finally:
            process.terminate()
            process.wait(timeout=15)
