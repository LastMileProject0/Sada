"""Offline transport fixtures. No test here claims real paid inference."""
import io
import json
from urllib.error import HTTPError, URLError

import pytest
from fastapi.testclient import TestClient
from sada_bridge.api import create_app
from sada_bridge import openrouter_provider as transport

MODEL = transport.MODEL
FAKE_KEY = 'unit-test-only-not-a-real-credential'


def reply(text='The field describes recommended action [SRC-01-E01].', **overrides):
    return {'model': MODEL, 'choices': [
        {'finish_reason': 'stop', 'message': {'content': text}}], **overrides}


class Response(io.BytesIO):
    status = 200


def install(monkeypatch, data=None, error=None, raw=None):
    calls = []

    class Opener:
        def open(self, req, timeout):
            calls.append((req, timeout))
            if error:
                raise error
            return Response(raw if raw is not None else json.dumps(data or reply()).encode())

    monkeypatch.setenv('OPENROUTER_API_KEY', FAKE_KEY)
    monkeypatch.setattr(transport.request, 'build_opener', lambda *_: Opener())
    return calls


def test_fixed_model_private_payload_and_limits(monkeypatch):
    calls = install(monkeypatch)
    assert transport.openrouter_provider('original prompt', MODEL).endswith('[SRC-01-E01].')
    req, timeout = calls[0]
    payload = json.loads(req.data)
    assert req.full_url == transport.ENDPOINT
    assert req.get_header('Authorization') == f'Bearer {FAKE_KEY}'
    assert timeout == 30
    assert payload == {
        'model': MODEL, 'messages': [{'role': 'user', 'content': 'original prompt'}],
        'temperature': 0, 'max_tokens': 700, 'stream': False,
        'provider': {'data_collection': 'deny', 'zdr': True,
                     'allow_fallbacks': False, 'require_parameters': True, 'only': ['phala']},
    }
    assert set(req.headers) == {'Authorization', 'Content-type'}


@pytest.mark.parametrize('mode', ['missing_key', 'wrong_model', 'oversized_prompt'])
def test_rejects_configuration_before_network(monkeypatch, mode):
    calls = install(monkeypatch)
    if mode == 'missing_key':
        monkeypatch.delenv('OPENROUTER_API_KEY')
    with pytest.raises(transport.ProviderUnavailable):
        transport.openrouter_provider(
            'x' * 24001 if mode == 'oversized_prompt' else 'prompt',
            'unapproved/model' if mode == 'wrong_model' else MODEL)
    assert not calls


@pytest.mark.parametrize('raw', [
    b'not json', b'[]', b'{}', b'x' * 65537,
    json.dumps(reply(model='another/model')).encode(),
    json.dumps(reply(FAKE_KEY)).encode(),
    json.dumps({'model': MODEL, 'error': {'message': FAKE_KEY}}).encode(),
    json.dumps({'model': MODEL, 'choices': [
        {'finish_reason': 'length', 'message': {'content': 'Truncated text'}}]}).encode(),
])
def test_rejects_invalid_truncated_or_wrong_model_response(monkeypatch, raw):
    install(monkeypatch, raw=raw)
    with pytest.raises(transport.ProviderUnavailable) as exc:
        transport.openrouter_provider('prompt', MODEL)
    assert FAKE_KEY not in str(exc.value)


@pytest.mark.parametrize('status', [302, 401, 402, 403, 429, 500, 503])
def test_provider_errors_are_sanitized(monkeypatch, status):
    install(monkeypatch, error=HTTPError(transport.ENDPOINT, status, FAKE_KEY, {},
                                        io.BytesIO(FAKE_KEY.encode())))
    with pytest.raises(transport.ProviderUnavailable) as exc:
        transport.openrouter_provider('prompt', MODEL)
    assert FAKE_KEY not in str(exc.value)


def test_network_timeout_and_redirect_rejected(monkeypatch):
    for exc in [URLError(FAKE_KEY), TimeoutError(FAKE_KEY)]:
        install(monkeypatch, error=exc)
        with pytest.raises(transport.ProviderUnavailable):
            transport.openrouter_provider('prompt', MODEL)
    assert transport._NoRedirect().redirect_request(None, None, 302, '', {},
                                                    'https://other.invalid') is None


@pytest.mark.parametrize(('question', 'draft'), [
    ('What does CAP say about the instruction field?',
     'This passage describes the content of the CAP instruction field [SRC-01-E01].'),
    ('ما معنى حقل instruction في معيار CAP؟',
     'تصف هذه الفقرة محتوى حقل instruction في معيار CAP [SRC-01-E01].'),
])
def test_original_pipeline_citations_and_private_data_boundary(tmp_path, monkeypatch, question, draft):
    calls = install(monkeypatch, data=reply(draft))
    with TestClient(create_app(tmp_path / 'test.sqlite')) as client:
        response = client.post('/api/policy/explain', json={'question': question},
                               headers={'X-SADA-Owner': 'b' * 64})
    data = response.json()
    assert response.status_code == 200
    assert data['explanation']['status'] == 'Answered'
    assert data['explanation']['model_id'] == MODEL
    assert data['explanation']['citations'][0]['passage_id'] == 'SRC-01-E01'
    sent = calls[0][0].data.decode()
    assert question in sent
    assert 'SCENARIO FACTS (read-only, not policy evidence): {}' in sent
    assert 'b' * 64 not in sent and FAKE_KEY not in sent
    assert 'evaluation_id' not in sent and 'owner_session_hash' not in sent
    assert FAKE_KEY not in response.text


def test_original_citation_retry_and_safety_guards(tmp_path, monkeypatch):
    calls = install(monkeypatch, data=reply('Unsupported claim [INVENTED].'))
    with TestClient(create_app(tmp_path / 'test.sqlite')) as client:
        response = client.post('/api/policy/explain',
                               json={'question': 'What does CAP say about the instruction field?'},
                               headers={'X-SADA-Owner': 'c' * 64})
    assert response.json()['explanation']['status'] == 'ReviewRequired'
    assert response.json()['explanation']['answer'] == ''
    assert len(calls) == 2
    assert 'FORMAT CORRECTION ONLY' in json.loads(calls[1][0].data)['messages'][0]['content']


def test_provider_outage_public_response_no_error_body(tmp_path, monkeypatch):
    install(monkeypatch, error=URLError(FAKE_KEY))
    with TestClient(create_app(tmp_path / 'test.sqlite')) as client:
        response = client.post('/api/policy/explain',
                               json={'question': 'What does CAP say about the instruction field?'},
                               headers={'X-SADA-Owner': 'd' * 64})
    result = response.json()['explanation']
    assert result['status'] == 'ModelUnavailable' and not result['answer']
    assert not result['llm_invoked']
    assert 'OpenRouter unavailable' in result['limitations'][0]
    assert FAKE_KEY not in response.text
