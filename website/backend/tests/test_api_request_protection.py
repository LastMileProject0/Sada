"""Capacity tests use temporary storage only; never delete existing results."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from pathlib import Path
from unittest.mock import patch
import json

import pytest
from fastapi.testclient import TestClient
from sada_bridge.api import create_app
from sada_bridge.storage import EvaluationStore, StorageCapacityReached, EvaluationBusy

SAMPLE = {'scenario': 'AL_WADI_FLASH_FLOOD', 'stage': 'T+04',
          'enabledChannelIds': ['CH01', 'CH02', 'CH03', 'CH04', 'CH05']}
OWNER_HEADERS = {'X-SADA-Owner': 'a' * 64}


@pytest.mark.parametrize(('headers', 'body', 'status'), [
    ({'content-type': 'text/plain'}, '{}', 415),
    ({'content-type': 'application/x-www-form-urlencoded'}, 'stage=T+04', 415),
    ({'content-type': 'application/json', 'content-encoding': 'gzip'}, 'compressed', 415),
    ({'content-type': 'application/json', 'content-encoding': 'br'}, 'compressed', 415),
    ({'content-type': 'application/json'}, ' ' * 4097, 413),
    ({'content-type': 'application/json'}, '{"broken":', 422),
])
def test_direct_python_request_boundary(tmp_path, headers, body, status):
    with patch('sada_bridge.api.run_ethar_integrated_recovery') as engine:
        with TestClient(create_app(tmp_path / 'test.sqlite'), headers=OWNER_HEADERS) as client:
            response = client.post('/api/evaluations', headers=headers, content=body)
            assert response.status_code == status
            engine.assert_not_called()


def test_streamed_request_limit_and_json_identity(tmp_path):
    with TestClient(create_app(tmp_path / 'test.sqlite'), headers=OWNER_HEADERS) as client:
        streamed = client.post('/api/evaluations',
                              headers={'content-type': 'application/json'},
                              content=iter([b' ' * 2048, b' ' * 2049]))
        assert streamed.status_code == 413
        normal = client.post('/api/evaluations', json=SAMPLE,
                             headers={'content-encoding': 'identity'})
        assert normal.status_code == 201


def test_no_queue_and_slot_is_held_until_engine_finishes(tmp_path):
    from sada_bridge.api import run_ethar_integrated_recovery as real_engine
    entered, release = Event(), Event()

    def held_engine(config):
        entered.set()
        assert release.wait(10)
        return real_engine(config)

    path = tmp_path / 'test.sqlite'
    with patch('sada_bridge.api.run_ethar_integrated_recovery', side_effect=held_engine) as engine:
        with TestClient(create_app(path), headers=OWNER_HEADERS) as first, TestClient(
                create_app(path), headers=OWNER_HEADERS) as second:
            with ThreadPoolExecutor(max_workers=2) as pool:
                pending = pool.submit(first.post, '/api/evaluations', json=SAMPLE)
                assert entered.wait(5)
                try:
                    busy = second.post('/api/evaluations', json=SAMPLE)
                    assert busy.status_code == 503
                    assert busy.headers['retry-after'] == '2'
                    assert engine.call_count == 1
                finally:
                    release.set()
                completed = pending.result(timeout=15)
                assert completed.status_code == 201
                again = second.post('/api/evaluations', json=SAMPLE)
                assert again.status_code == 201


def test_storage_full_preserves_existing_id_and_rejects_before_execution(tmp_path):
    path = tmp_path / 'test.sqlite'
    with patch('sada_bridge.storage.MAX_RESULTS', 1):
        with TestClient(create_app(path), headers=OWNER_HEADERS) as client:
            first = client.post('/api/evaluations', json=SAMPLE)
            assert first.status_code == 201
            ident = first.json()['id']
            original = client.get(f'/api/evaluations/{ident}').json()
            with patch('sada_bridge.api.run_ethar_integrated_recovery') as engine:
                rejected = client.post('/api/evaluations', json=SAMPLE)
                assert rejected.status_code == 503
                engine.assert_not_called()
        with TestClient(create_app(path), headers=OWNER_HEADERS) as restored:
            assert restored.get(f'/api/evaluations/{ident}').json() == original


def test_byte_capacity_and_lock_release_on_exception(tmp_path):
    store = EvaluationStore(tmp_path / 'test.sqlite')
    with patch('sada_bridge.storage.MAX_RESULT_BYTES', 10):
        with pytest.raises(StorageCapacityReached):
            store.save({'id': 'oversized', 'value': 'x' * 20})
    payload = {'id': 'one', 'value': 'x' * 10}
    size = len(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode())
    with patch('sada_bridge.storage.MAX_TOTAL_BYTES', size + 1):
        store.save(payload, OWNER_HEADERS['X-SADA-Owner'])
        with pytest.raises(StorageCapacityReached):
            store.save({'id': 'two'})
    assert store.load('one', OWNER_HEADERS['X-SADA-Owner']) == payload
    assert store.load('two', OWNER_HEADERS['X-SADA-Owner']) is None
    with patch('sada_bridge.storage.MAX_DATABASE_BYTES', store.path.stat().st_size):
        with pytest.raises(StorageCapacityReached):
            store.check_capacity()
    with pytest.raises(RuntimeError):
        with store.execution_slot():
            raise RuntimeError('test only')
    with store.execution_slot():
        with pytest.raises(EvaluationBusy):
            with EvaluationStore(store.path).execution_slot():
                pytest.fail('A second execution must not be admitted')


def test_failed_engine_does_not_leave_capacity_locked(tmp_path):
    with TestClient(create_app(tmp_path / 'test.sqlite'), headers=OWNER_HEADERS) as client:
        with patch('sada_bridge.api.run_ethar_integrated_recovery', side_effect=RuntimeError('private')):
            response = client.post('/api/evaluations', json=SAMPLE)
            assert response.status_code == 500
            assert response.json() == {'detail': 'Evaluation failed'}
        assert client.post('/api/evaluations', json=SAMPLE).status_code == 201
