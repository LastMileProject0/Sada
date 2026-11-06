"""SQLite persistence of *aggregated* evaluation result only (no resident rows)."""
from __future__ import annotations
import json
import sqlite3
import fcntl
from contextlib import contextmanager
from pathlib import Path
from .migrations import ensure_ownership_schema

MAX_RESULTS = 500
MAX_RESULT_BYTES = 256 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_DATABASE_BYTES = 64 * 1024 * 1024


class EvaluationBusy(Exception):
    pass


class StorageCapacityReached(Exception):
    pass


class StorageUnavailable(RuntimeError):
    """Fixed safe messages only; never include a connection string."""


class EvaluationStore:
    def __init__(self, db_path: str | Path):
        self.path = Path(db_path)
        ensure_ownership_schema(self.path)

    def _connect(self):
        return sqlite3.connect(self.path, timeout=15)

    @contextmanager
    def execution_slot(self):
        # Nonblocking OS lock survives request cancellation and spans processes
        # sharing this database. No in-memory queue or schema migration.
        with self.path.with_suffix(self.path.suffix + '.lock').open('a') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise EvaluationBusy() from None
            try:
                self.check_capacity()
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def _check_capacity(self, conn, incoming_bytes=0):
        count, size = conn.execute(
            'SELECT COUNT(*), COALESCE(SUM(length(CAST(result AS BLOB))), 0) '
            'FROM evaluation_results').fetchone()
        if (count >= MAX_RESULTS or size + incoming_bytes >= MAX_TOTAL_BYTES
                or self.path.stat().st_size >= MAX_DATABASE_BYTES):
            raise StorageCapacityReached()

    def check_capacity(self):
        with self._connect() as conn:
            self._check_capacity(conn)

    def check_readable(self):
        # Readiness must never recreate a missing database or migrate anything.
        uri = self.path.resolve().as_uri() + '?mode=ro'
        with sqlite3.connect(uri, uri=True, timeout=1) as conn:
            conn.execute('SELECT id, owner_session_hash FROM evaluation_results LIMIT 1').fetchall()

    def save(self, result: dict, owner_session_hash: str | None = None):
        serialized = json.dumps(result, ensure_ascii=False, allow_nan=False)
        size = len(serialized.encode('utf-8'))
        if size > MAX_RESULT_BYTES:
            raise StorageCapacityReached()
        with self._connect() as conn:
            page_size = conn.execute('PRAGMA page_size').fetchone()[0]
            conn.execute(f'PRAGMA max_page_count = {MAX_DATABASE_BYTES // page_size}')
            conn.execute('BEGIN IMMEDIATE')
            self._check_capacity(conn, size)
            try:
                conn.execute('INSERT INTO evaluation_results (id, result, owner_session_hash) '
                             'VALUES (?, ?, ?)', (result['id'], serialized, owner_session_hash))
            except sqlite3.OperationalError as error:
                if error.sqlite_errorcode == sqlite3.SQLITE_FULL:
                    raise StorageCapacityReached() from None
                raise

    def load(self, evaluation_id: str, owner_session_hash: str | None = None):
        if not owner_session_hash:
            return None
        with self._connect() as conn:
            row = conn.execute('SELECT result FROM evaluation_results '
                               'WHERE id = ? AND owner_session_hash = ?',
                               (evaluation_id, owner_session_hash)).fetchone()
        return json.loads(row[0]) if row else None
