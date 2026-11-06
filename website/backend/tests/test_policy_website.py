import fcntl
from fastapi.testclient import TestClient
from sada_bridge.api import create_app

OWNER = {'X-SADA-Owner': 'a' * 64}
QUESTION = {'question': 'What does CAP say about the instruction field?'}


def test_actual_retrieval_with_unavailable_model(tmp_path, monkeypatch):
    # Unit-test unavailable transport deliberately; not a real inference test.
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    with TestClient(create_app(tmp_path / 'test.sqlite')) as client:
        response = client.post('/api/policy/explain', json=QUESTION, headers=OWNER)
    assert response.status_code == 200
    data = response.json()
    assert data['retrieval']['evidence_items'][0]['evidence_id'] == 'SRC-01-E01'
    assert data['explanation']['status'] == 'ModelUnavailable'
    assert data['explanation']['llm_invoked'] is False
    assert data['explanation']['answer'] == ''
    assert data['explanation']['citations'] == []


def test_unsupported_question_never_calls_provider(tmp_path, monkeypatch):
    def forbidden(*_):
        raise AssertionError('Unsupported questions must not invoke a model')
    monkeypatch.setattr('sada_bridge.policy.openrouter_provider', forbidden)
    with TestClient(create_app(tmp_path / 'test.sqlite')) as client:
        response = client.post('/api/policy/explain', headers=OWNER, json={
            'question': 'What will the train ticket price in Kyoto be on 19 December 2042?'})
    data = response.json()
    assert data['retrieval']['status'] == 'INSUFFICIENT_EVIDENCE'
    assert data['explanation']['status'] == 'InsufficientInformation'
    assert data['explanation']['llm_invoked'] is False


def test_policy_input_and_internal_boundary(tmp_path):
    with TestClient(create_app(tmp_path / 'test.sqlite')) as client:
        assert client.post('/api/policy/explain', json=QUESTION).status_code == 404
        for body in [{'question': ' '}, {'question': 'x' * 1201},
                     {**QUESTION, 'model': 'other'}, {**QUESTION, 'url': 'http://evil.invalid'}]:
            assert client.post('/api/policy/explain', json=body, headers=OWNER).status_code == 422
        assert client.post('/api/policy/explain', content='x' * 5000,
                           headers={**OWNER, 'Content-Type': 'application/json'}).status_code == 413
        assert client.post('/api/policy/explain', content='hello',
                           headers={**OWNER, 'Content-Type': 'text/plain'}).status_code == 415


def test_policy_inference_has_no_waiting_queue(tmp_path):
    with TestClient(create_app(tmp_path / 'test.sqlite')) as client:
        with (tmp_path / 'policy.lock').open('a') as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            response = client.post('/api/policy/explain', json=QUESTION, headers=OWNER)
            assert response.status_code == 503
            assert response.headers['Retry-After'] == '3'
    assert not list(tmp_path.glob('*question*'))
