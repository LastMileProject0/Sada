"""Development rehearsal tools ONLY. Never production DDL, startup or build hooks.

Default action validates a separately approved SQLite BACKUP read-only.
All target mutations require explicit opt-in and a dedicated development DSN.
Never pass a connection string on the command line.
"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))

from sada_bridge.postgres import PostgresEvaluationStore
from sada_bridge.postgres_schema import CAPACITY_LOCK, EXECUTION_LOCK, check_schema
from sada_bridge.storage import EvaluationBusy
from sada_bridge.storage_transfer import fingerprint, import_snapshot, read_snapshot


def apply_development_schema(store):
    with store.connection() as conn:
        for key in (EXECUTION_LOCK, CAPACITY_LOCK):
            if not conn.execute('SELECT pg_try_advisory_xact_lock(%s)', (key,)).fetchone()[0]:
                raise EvaluationBusy()
        sql = (ROOT / 'backend/sada_bridge/postgres_schema.sql').read_text()
        conn.execute(sql, prepare=False)
        check_schema(conn)  # Incompatible existing schema aborts the whole transaction.


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-backup', type=Path)
    parser.add_argument('--apply-development-schema', action='store_true')
    parser.add_argument('--import-development-snapshot', action='store_true')
    parser.add_argument('--confirm-development-target', action='store_true')
    args = parser.parse_args(argv)
    try:
        # Never read a production DSN or perform production DDL/data cutover.
        if os.environ.get('NODE_ENV') == 'production':
            raise ValueError()
        if args.apply_development_schema and args.import_development_snapshot:
            raise ValueError()  # Schema and data are separately approved actions.
        rows = read_snapshot(args.source_backup) if args.source_backup else None
        mutation = args.apply_development_schema or args.import_development_snapshot
        if not mutation:
            if rows is None:
                raise ValueError()
            print(json.dumps({'mode': 'read-only-backup-validation', 'rows': len(rows),
                              'field_fingerprint': fingerprint(rows)}))
            return 0
        if not args.confirm_development_target:
            raise ValueError()
        # This separately named secret must be independently confirmed as DEV.
        dsn = os.environ.get('SADA_DEV_POSTGRES_DSN', '')
        if not dsn:
            raise ValueError()
        store = PostgresEvaluationStore(dsn)
        if args.apply_development_schema:
            apply_development_schema(store)
            print(json.dumps({'development_schema': 'validated', 'data_imported': False}))
        else:
            if rows is None:
                raise ValueError()
            print(json.dumps(import_snapshot(store, rows)))
        return 0
    except Exception:
        # No DSN, row values, IDs, owners or raw database messages.
        print('Preparation blocked or failed; no partial import committed. '
              'Check explicit development approval, configuration, snapshot and schema.',
              file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
