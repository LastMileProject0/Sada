"""SADA FastAPI add-on. Endpoints are NEW (not claimed to exist in original repo).

Run from the original integrated Python repository root with the add-on folder
alongside lastmile_ai/: uvicorn sada_bridge.api:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations
import os
import re
from pathlib import Path
from uuid import uuid4, UUID
from fastapi import FastAPI, HTTPException, Header
from .contract import EvaluationRequest
from .normalize import normalize_result, simulation_summary
from .storage import EvaluationStore, EvaluationBusy, StorageCapacityReached, StorageUnavailable
from .storage_backend import create_store, ResultStore
from .request_protection import EvaluationRequestBoundary
from .policy import create_policy_router
from lastmile_ai.agents.ethar_stage_bridge import run_ethar_integrated_recovery


def create_app(db_path: str | Path | None = None, *, storage: ResultStore | None = None) -> FastAPI:
    app = FastAPI(title='SADA Verified Evaluation Adapter', version='0.1.0')
    # This loopback service has no browser cross-origin callers.
    app.add_middleware(EvaluationRequestBoundary)
    store = storage if storage is not None else create_store(db_path)
    # Existing AI pipeline remains unchanged; only its local coordination folder
    # is independent of the optional external result-store connection.
    control_dir = store.path.parent if isinstance(store, EvaluationStore) else Path('.sada_api')
    app.include_router(create_policy_router(control_dir))

    @app.get('/api/health')
    def health():
        try:
            store.check_readable()
            dataset = Path(__file__).resolve().parents[1] / 'data/reference/LastMile_AI_Step1_Master_Dataset.xlsx'
            if not dataset.is_file() or not os.access(dataset, os.R_OK):
                raise OSError()
        except Exception:
            raise HTTPException(status_code=503, detail='Evaluation service unavailable') from None
        return {'status': 'ok', 'service': 'sada-evaluation-adapter'}

    @app.post('/api/evaluations', status_code=201)
    def evaluate(body: EvaluationRequest,
                 owner: str | None = Header(default=None, alias='X-SADA-Owner')):
        if not owner or not re.fullmatch(r'[0-9a-f]{64}', owner):
            raise HTTPException(status_code=404, detail='Evaluation not found')
        config = body.to_engine_configuration()
        # Intentionally synchronous endpoint: FastAPI runs it in a threadpool.
        # Only the approved stage-aware entrypoint executes the engine.
        try:
            with store.execution_slot():
                run = run_ethar_integrated_recovery(config)
                evaluation_id = str(uuid4())
                data = normalize_result(run, config, evaluation_id)
                store.save(data, owner)
        except EvaluationBusy:
            raise HTTPException(status_code=503, detail='Evaluation capacity reached. Please retry later.',
                                headers={'Retry-After': '2'}) from None
        except StorageCapacityReached:
            raise HTTPException(status_code=503, detail='Evaluation storage capacity reached. Existing results remain available.') from None
        except StorageUnavailable:
            raise HTTPException(status_code=503, detail='Evaluation storage unavailable') from None
        except Exception:
            # No resident data, source paths or raw exceptions in public HTTP responses.
            raise HTTPException(status_code=500, detail='Evaluation failed') from None
        return simulation_summary(data)

    @app.get('/api/evaluations/{evaluation_id}')
    def get_evaluation(evaluation_id: str,
                       owner: str | None = Header(default=None, alias='X-SADA-Owner')):
        if not owner or not re.fullmatch(r'[0-9a-f]{64}', owner):
            raise HTTPException(status_code=404, detail='Evaluation not found')
        try:
            normalized_id = str(UUID(evaluation_id))
        except (ValueError, AttributeError):
            raise HTTPException(status_code=404, detail='Evaluation not found') from None
        try:
            data = store.load(normalized_id, owner)
        except StorageUnavailable:
            raise HTTPException(status_code=503, detail='Evaluation storage unavailable') from None
        if data is None:
            raise HTTPException(status_code=404, detail='Evaluation not found')
        return data

    return app


app = create_app()
