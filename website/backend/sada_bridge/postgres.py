"""Opt-in private PostgreSQL result store. No DDL or fallback at runtime."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import threading

import psycopg
from psycopg.conninfo import conninfo_to_dict

from .postgres_schema import CAPACITY_LOCK, EXECUTION_LOCK, OWNER, check_schema, validate_row
from .storage import (
    MAX_RESULTS, MAX_TOTAL_BYTES, EvaluationBusy, StorageCapacityReached, StorageUnavailable,
)


class PostgresEvaluationStore:
    def __init__(self, dsn: str, *, production=False):
        try:
            options = conninfo_to_dict(dsn)
            if not options.get('dbname') or not options.get('host'):
                raise ValueError()
            if production and options.get('sslmode') != 'verify-full':
                raise ValueError()
        except Exception:
            raise StorageUnavailable('Explicit PostgreSQL configuration unavailable') from None
        self._dsn = dsn
        self._production = production
        self._local = threading.local()

    @contextmanager
    def connection(self, *, readiness=False):
        try:
            with psycopg.connect(
                self._dsn, connect_timeout=1 if readiness else 3,
                application_name='sada-evaluation',
                options='-c statement_timeout=1000 -c lock_timeout=1000' if readiness
                else '-c statement_timeout=5000 -c lock_timeout=1000',
            ) as conn:
                conn.execute('SET TRANSACTION ISOLATION LEVEL READ COMMITTED')
                yield conn
        except (psycopg.Error, OSError):
            raise StorageUnavailable('Evaluation database unavailable') from None

    def check_readable(self):
        with self.connection(readiness=True) as conn:
            check_schema(conn, runtime=self._production)

    @staticmethod
    def capacity(conn, incoming_bytes=0, incoming_count=1):
        count, size = conn.execute(
            'SELECT COUNT(*), COALESCE(SUM(octet_length(result)), 0) '
            'FROM public.evaluation_results').fetchone()
        if count + incoming_count > MAX_RESULTS or size + incoming_bytes >= MAX_TOTAL_BYTES:
            raise StorageCapacityReached()

    @contextmanager
    def execution_slot(self):
        if getattr(self._local, 'connection', None) is not None:
            raise EvaluationBusy()
        with self.connection() as conn:
            if not conn.execute('SELECT pg_try_advisory_xact_lock(%s)',
                                (EXECUTION_LOCK,)).fetchone()[0]:
                raise EvaluationBusy()
            self.capacity(conn)
            self._local.connection = conn
            try:
                yield
            finally:
                self._local.connection = None
        # Connection context commits/rolls back and releases the transaction lock.

    def _save(self, conn, row):
        # Nonwaiting shared lock across instances and migration rehearsal tools.
        if not conn.execute('SELECT pg_try_advisory_xact_lock(%s)',
                            (CAPACITY_LOCK,)).fetchone()[0]:
            raise EvaluationBusy()
        self.capacity(conn, len(row[1].encode('utf-8')))
        conn.execute(
            'INSERT INTO public.evaluation_results '
            '(id, result, created_at, owner_session_hash) VALUES (%s, %s, %s, %s)', row)

    def save(self, result: dict, owner_session_hash: str | None = None):
        raw = json.dumps(result, ensure_ascii=False, allow_nan=False)
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        row = validate_row((result['id'], raw, timestamp, owner_session_hash))
        active = getattr(self._local, 'connection', None)
        if active is not None:
            self._save(active, row)
        else:
            with self.connection() as conn:
                self._save(conn, row)

    def load(self, evaluation_id: str, owner_session_hash: str | None = None):
        if not isinstance(owner_session_hash, str) or OWNER.fullmatch(owner_session_hash) is None:
            return None
        with self.connection() as conn:
            row = conn.execute(
                'SELECT result FROM public.evaluation_results '
                'WHERE id = %s AND owner_session_hash = %s',
                (evaluation_id, owner_session_hash)).fetchone()
        return json.loads(row[0]) if row else None
