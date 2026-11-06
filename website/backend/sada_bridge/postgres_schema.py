"""Read-only schema validation and shared limits for the optional PG adapter."""
import json
import re
from datetime import datetime
from uuid import UUID

from .storage import MAX_RESULT_BYTES, StorageCapacityReached, StorageUnavailable

EXECUTION_LOCK = 1396786241
CAPACITY_LOCK = 1396786242
OWNER = re.compile(r'[0-9a-f]{64}')
TABLE = 'public.evaluation_results'


def validate_row(row):
    evaluation_id, raw, created_at, owner = row
    if not isinstance(evaluation_id, str) or str(UUID(evaluation_id)) != evaluation_id:
        raise ValueError('Invalid evaluation identifier')
    if not isinstance(raw, str) or len(raw.encode('utf-8')) > MAX_RESULT_BYTES:
        raise StorageCapacityReached()
    def invalid_constant(_):
        raise ValueError('Nonfinite JSON is unsupported')
    value = json.loads(raw, parse_constant=invalid_constant)
    if not isinstance(value, dict) or value.get('id') != evaluation_id:
        raise ValueError('Invalid evaluation object')
    if not isinstance(created_at, str) or not 1 <= len(created_at) <= 128:
        raise ValueError('Invalid evaluation timestamp')
    datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    if owner is not None and (not isinstance(owner, str) or OWNER.fullmatch(owner) is None):
        raise ValueError('Invalid evaluation ownership')
    return row  # Original strings/NULL, not canonicalized or reassigned.


def check_schema(conn, *, runtime=False):
    columns = conn.execute("""
        SELECT a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod), a.attnotnull
        FROM pg_catalog.pg_attribute a
        WHERE a.attrelid = to_regclass('public.evaluation_results')
          AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum
    """).fetchall()
    if columns != [('id', 'text', True), ('result', 'text', True),
                   ('created_at', 'text', True), ('owner_session_hash', 'text', False)]:
        raise StorageUnavailable('Evaluation database schema unavailable')
    constraints = conn.execute("""
        SELECT conname, contype, pg_get_constraintdef(oid)
        FROM pg_catalog.pg_constraint
        WHERE conrelid = to_regclass('public.evaluation_results')
    """).fetchall()
    compact = lambda text: re.sub(r'[\s()]', '', text)
    definitions = {name: (kind, compact(definition)) for name, kind, definition in constraints}
    expected = {
        'evaluation_results_pkey': ('p', 'PRIMARYKEYid'),
        'evaluation_results_result_bytes': ('c', 'CHECKoctet_lengthresult<=262144'),
        'evaluation_results_result_object': ('c', "CHECKjsonb_typeofresult::jsonb='object'::text"),
        'evaluation_results_owner_format': ('c', "CHECKowner_session_hash~'^[0-9a-f]{64}$'::text"),
    }
    if any(definitions.get(k) != v for k, v in expected.items()):
        raise StorageUnavailable('Evaluation database constraints unavailable')
    index = conn.execute("""
        SELECT pg_get_indexdef(i.indexrelid, 1, true),
               pg_get_indexdef(i.indexrelid, 2, true),
               pg_get_expr(i.indpred, i.indrelid)
        FROM pg_catalog.pg_index i
        WHERE i.indexrelid = to_regclass('public.evaluation_results_owner_id')
          AND i.indrelid = to_regclass('public.evaluation_results')
          AND i.indisvalid AND i.indisready AND i.indnatts = 2
    """).fetchone()
    if not index or index[:2] != ('owner_session_hash', 'id') or compact(index[2]) != 'owner_session_hashISNOTNULL':
        raise StorageUnavailable('Evaluation database index unavailable')
    # Check actual SELECT permission and all approved columns, without reading rows.
    conn.execute('SELECT id, result, created_at, owner_session_hash FROM public.evaluation_results LIMIT 0')
    if runtime:
        privileges = conn.execute("""
            SELECT has_table_privilege(current_user, 'public.evaluation_results', 'INSERT'),
                   has_table_privilege(current_user, 'public.evaluation_results', 'UPDATE'),
                   has_table_privilege(current_user, 'public.evaluation_results', 'DELETE'),
                   has_table_privilege(current_user, 'public.evaluation_results', 'TRUNCATE')
        """).fetchone()
        if privileges != (True, False, False, False):
            raise StorageUnavailable('Least-privilege evaluation database role required')
