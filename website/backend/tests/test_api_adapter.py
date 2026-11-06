"""Run with original integrated repository on PYTHONPATH and this add-on on PYTHONPATH."""
import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sada_bridge.api import create_app
from sada_bridge.contract import EvaluationRequest

FULL_CHANNELS = ['CH01','CH02','CH03','CH04','CH05']
OWNER_HEADERS = {'X-SADA-Owner': 'a' * 64}
SAMPLE = {'scenario': 'AL_WADI_FLASH_FLOOD',
          'stage': 'T+04', 'enabledChannelIds': FULL_CHANNELS}


def test_stage_mapping_and_input_whitelist():
    assert EvaluationRequest(**SAMPLE).to_engine_configuration().selected_stage.value == 'T+04:00'
    for stage in ['T+00', 'T+02', 'T+04', 'T+06']:
        assert EvaluationRequest(**{**SAMPLE, 'stage': stage}).canonical_web_config()['stage'] == stage


def test_validation_rejects_invalid_requests():
    with TemporaryDirectory() as tmp:
        with TestClient(create_app(Path(tmp)/'storage.sqlite'), headers=OWNER_HEADERS) as client:
            bad = [
                {**SAMPLE, 'stage': 'T+07'},
                {**SAMPLE, 'scenario': 'invented'},
                {**SAMPLE, 'enabledChannelIds': []},
                {**SAMPLE, 'enabledChannelIds': ['CH01','CH01']},
                {**SAMPLE, 'enabledChannelIds': ['CH99']},
                {**SAMPLE, 'extraField': 'not allowed'},
            ]
            for item in bad:
                response = client.post('/api/evaluations', json=item)
                assert response.status_code == 422, response.text
            assert client.get('/api/evaluations/1234').status_code == 404
            assert client.get('/api/evaluations/00000000-0000-4000-8000-000000000000').status_code == 404


def test_actual_t04_run_and_results_survive_new_process_like_client():
    with TemporaryDirectory() as tmp:
        path = Path(tmp)/'persisted.sqlite'
        with TestClient(create_app(path), headers=OWNER_HEADERS) as client:
            response = client.post('/api/evaluations', json=SAMPLE)
            assert response.status_code == 201, response.text
            simulation = response.json()
            assert simulation['configuration'] == SAMPLE
            assert set(simulation['outputs']) == {'delivery','risk','accessibility','policy','recovery','trace'}
            ident = simulation['id']
            assert re.fullmatch(r'[0-9a-f-]{36}', ident)
            data = client.get(f'/api/evaluations/{ident}').json()
            assert data['source'] == 'backend'
            assert data['configuration']['population'] == 1000
            assert data['recommendedPlanId'] == 'P3'
            assert [p['id'] for p in data['plans']] == ['P0','P1','P2','P3']
            plans = {p['id']:p for p in data['plans']}
            assert plans['P0']['metrics']['reach']['value'] == 722
            assert plans['P0']['metrics']['effective']['value'] == 0
            assert plans['P0']['metrics']['critical']['value'] == 278
            assert plans['P3']['metrics']['reach']['value'] == 942
            assert plans['P3']['metrics']['effective']['value'] == 366
            assert plans['P3']['metrics']['critical']['value'] == 58
            assert plans['P3']['metrics']['recovery']['value'] == 36.6
            assert plans['P3']['metrics']['recovery']['unit'] == 'percent'
            assert plans['P0']['accessibility']['uniqueResidentsWithGaps'] is None
            assert all(len(p['channels']) == 5 for p in data['plans'])
            assert len({p['id'] for p in data['plans']}) == len(data['plans'])
            assert data['explanation']['source'] == 'backend'
            assert data['explanation']['reason']['ar'] is None
            assert data['explanation']['reason']['en']
            serialized = json.dumps(data)
            assert 'resident_id' not in serialized and 'Residents sheet' not in serialized
            assert 'source_registry' not in serialized
        # New app+client attached to the same on-disk database: refresh/restart case.
        with TestClient(create_app(path), headers=OWNER_HEADERS) as second_client:
            restored = second_client.get(f'/api/evaluations/{ident}')
            assert restored.status_code == 200
            assert restored.json() == data


def test_configuration_changes_drive_real_rerun():
    with TemporaryDirectory() as tmp:
        with TestClient(create_app(Path(tmp)/'storage.sqlite'), headers=OWNER_HEADERS) as client:
            other = {**SAMPLE, 'stage':'T+02', 'enabledChannelIds':['CH03','CH04','CH05']}
            r = client.post('/api/evaluations', json=other)
            assert r.status_code == 201
            sim = r.json()
            assert sim['configuration'] == other
            db = client.get(f'/api/evaluations/{sim["id"]}').json()
            assert db['configuration']['stage'] == 'T+02'
            assert db['configuration']['enabledChannelIds'] == other['enabledChannelIds']
            assert db['source'] == 'backend'
            # Disabled channels had no selected delivery attempt in the actual rerun.
            for p in db['plans']:
                for c in p['channels']:
                    if c['id'] in ('CH01','CH02'):
                        assert c['selectedAttempts'] == 0


def test_loopback_service_has_no_browser_cors(monkeypatch):
    monkeypatch.setenv('SADA_ALLOWED_ORIGINS', 'https://trusted.example')
    with TemporaryDirectory() as tmp:
        with TestClient(create_app(Path(tmp)/'storage.sqlite'), headers=OWNER_HEADERS) as client:
            a = client.options('/api/evaluations', headers={
                'origin':'https://trusted.example', 'access-control-request-method':'POST'})
            b = client.options('/api/evaluations', headers={
                'origin':'https://untrusted.example', 'access-control-request-method':'POST'})
            assert a.status_code == b.status_code == 405
            assert 'access-control-allow-origin' not in a.headers
            assert 'access-control-allow-origin' not in b.headers


def test_all_approved_stages_execute_real_engine():
    with TemporaryDirectory() as tmp:
        with TestClient(create_app(Path(tmp)/'storage.sqlite'), headers=OWNER_HEADERS) as client:
            for stage in ['T+00', 'T+02', 'T+04', 'T+06']:
                response = client.post('/api/evaluations', json={**SAMPLE, 'stage': stage})
                assert response.status_code == 201, (stage, response.text)
                result = client.get(f'/api/evaluations/{response.json()["id"]}')
                assert result.status_code == 200
                body = result.json()
                assert body['configuration']['stage'] == stage
                assert body['recommendedPlanId'] in [p['id'] for p in body['plans']]
                assert body['plans'][0]['id'] == 'P0'
                for plan in body['plans']:
                    for name in ('reach','effective','critical'):
                        assert 0 <= plan['metrics'][name]['value'] <= 1000
