"""Explicit backend selection. Managed DATABASE_URL never selects storage."""
import os
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Protocol

from .storage import EvaluationStore, StorageUnavailable


class ResultStore(Protocol):
    def save(self, result: dict, owner_session_hash: str | None = None): ...
    def load(self, evaluation_id: str, owner_session_hash: str | None = None): ...
    def check_readable(self): ...
    def execution_slot(self) -> AbstractContextManager: ...


def create_store(db_path: str | Path | None = None, *, environ=None, production=None) -> ResultStore:
    env = os.environ if environ is None else environ
    prod = env.get('NODE_ENV') == 'production' if production is None else production
    backend = env.get('SADA_STORAGE_BACKEND', 'sqlite')
    if prod and (backend != 'postgres' or db_path is not None):
        raise StorageUnavailable('Production requires explicit durable PostgreSQL storage')
    if db_path is not None:
        return EvaluationStore(db_path)  # Existing explicit temporary/local tests.
    if backend == 'sqlite':
        return EvaluationStore(env.get('SADA_EVAL_DB', '.sada_api/evaluations.sqlite3'))
    if backend == 'postgres':
        dsn = env.get('SADA_POSTGRES_DSN', '')
        if not dsn:
            raise StorageUnavailable('Explicit PostgreSQL configuration unavailable')
        from .postgres import PostgresEvaluationStore
        return PostgresEvaluationStore(dsn, production=prod)
    raise StorageUnavailable('Unsupported evaluation storage backend')
