"""Explicit development rehearsal only; source SQLite is opened read-only."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

from .postgres_schema import CAPACITY_LOCK, EXECUTION_LOCK, check_schema, validate_row
from .storage import MAX_RESULTS, MAX_TOTAL_BYTES, EvaluationBusy, StorageCapacityReached


def fingerprint(rows):
    digest = hashlib.sha256()
    for row in sorted(rows):
        digest.update(json.dumps(row, ensure_ascii=False).encode('utf-8'))
        digest.update(b'\n')
    return digest.hexdigest()


def read_snapshot(path):
    path = Path(path).resolve(strict=True)
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as conn:
        conn.execute('PRAGMA query_only = ON')
        conn.execute('BEGIN')
        if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('SQLite snapshot integrity failed')
        columns = {r[1] for r in conn.execute('PRAGMA table_info(evaluation_results)')}
        if not {'id', 'result', 'created_at'} <= columns:
            raise ValueError('SQLite snapshot schema unavailable')
        owner = 'owner_session_hash' if 'owner_session_hash' in columns else 'NULL'
        rows = conn.execute(
            'SELECT id, result, created_at, ' + owner +
            ' FROM evaluation_results ORDER BY id LIMIT ?', (MAX_RESULTS + 1,)).fetchall()
        for row in rows:
            validate_row(row)
        if len(rows) > MAX_RESULTS or sum(len(r[1].encode('utf-8')) for r in rows) >= MAX_TOTAL_BYTES:
            raise StorageCapacityReached()
        return rows


def import_snapshot(store, rows):
    # Validate everything BEFORE connecting; caller must separately authorize.
    for row in rows:
        validate_row(row)
    if len(rows) > MAX_RESULTS or sum(len(r[1].encode('utf-8')) for r in rows) >= MAX_TOTAL_BYTES:
        raise StorageCapacityReached()
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('Duplicate snapshot identifiers')
    with store.connection() as conn:
        for key in (EXECUTION_LOCK, CAPACITY_LOCK):
            if not conn.execute('SELECT pg_try_advisory_xact_lock(%s)', (key,)).fetchone()[0]:
                raise EvaluationBusy()
        check_schema(conn)
        store.capacity(conn, incoming_count=0)
        inserted = 0
        for row in rows:
            existing = conn.execute(
                'SELECT id, result, created_at, owner_session_hash '
                'FROM public.evaluation_results WHERE id = %s', (row[0],)).fetchone()
            if existing is not None:
                if tuple(existing) != tuple(row):
                    raise ValueError('Snapshot conflict; import rolled back')
                continue
            store.capacity(conn, len(row[1].encode('utf-8')))
            conn.execute('INSERT INTO public.evaluation_results '
                         '(id, result, created_at, owner_session_hash) VALUES (%s, %s, %s, %s)', row)
            inserted += 1
        copied = [conn.execute(
            'SELECT id, result, created_at, owner_session_hash '
            'FROM public.evaluation_results WHERE id = %s', (row[0],)).fetchone() for row in rows]
        if copied != rows:
            raise ValueError('Snapshot verification failed; import rolled back')
        return {'rows': len(rows), 'inserted': inserted, 'identical_existing': len(rows) - inserted,
                'field_fingerprint': fingerprint(rows)}
