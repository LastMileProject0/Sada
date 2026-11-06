"""Approved additive ownership migration, with a verified private SQLite backup."""
from contextlib import closing
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from uuid import uuid4


def _fingerprint(conn):
    digest = hashlib.sha256()
    count = 0
    for row in conn.execute(
            'SELECT id, result, created_at FROM evaluation_results ORDER BY id'):
        digest.update(json.dumps(row, ensure_ascii=False).encode('utf-8'))
        count += 1
    return count, digest.hexdigest()


def ensure_ownership_schema(db_path: str | Path):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with closing(sqlite3.connect(path, timeout=15)) as ready:
            if any(row[1] == 'owner_session_hash' for row in ready.execute(
                    'PRAGMA table_info(evaluation_results)')):
                return {'migrated': False, 'created': False}
    # Same lock used for execution: no evaluation may overlap this migration.
    with path.with_suffix(path.suffix + '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with closing(sqlite3.connect(path, timeout=15)) as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                columns = {row[1] for row in conn.execute(
                    'PRAGMA table_info(evaluation_results)')}
                if not columns:
                    conn.execute('CREATE TABLE evaluation_results ('
                                 'id TEXT PRIMARY KEY, result TEXT NOT NULL, '
                                 'created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, '
                                 'owner_session_hash TEXT)')
                    conn.commit()
                    return {'migrated': False, 'created': True}
                if 'owner_session_hash' in columns:
                    conn.commit()
                    return {'migrated': False, 'created': False}
                original = _fingerprint(conn)
                backups = path.parent / 'backups'
                backups.mkdir(mode=0o700, exist_ok=True)
                backup = backups / f'{path.name}.pre-ownership-{uuid4().hex}.sqlite3'
                fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                os.close(fd)
                # Separate reader: the write reservation above prevents changes
                # but permits a consistent online backup without self-deadlock.
                with closing(sqlite3.connect(path)) as source, closing(
                        sqlite3.connect(backup)) as target:
                    source.backup(target)
                    if (target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok'
                            or _fingerprint(target) != original):
                        raise RuntimeError('Pre-migration backup verification failed')
                conn.execute('ALTER TABLE evaluation_results ADD COLUMN owner_session_hash TEXT')
                if _fingerprint(conn) != original:
                    raise RuntimeError('Migration data verification failed')
                conn.commit()
                return {'migrated': True, 'backup': str(backup),
                        'preserved_rows': original[0], 'integrity': 'ok'}
            except BaseException:
                conn.rollback()
                raise


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('database')
    args = parser.parse_args()
    print(json.dumps(ensure_ownership_schema(args.database)))
