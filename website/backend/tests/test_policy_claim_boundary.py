"""Approved narrow-scope regressions. Synthetic old holdout labels stay frozen."""
import copy
from dataclasses import replace
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from holdout.run_policy_grounding import load_cases, no_network
from lastmile_ai.ai.policy_explainer import explain_policy
from lastmile_ai.ai.maymona_rag_bridge import to_policy_retrieval
from lastmile_ai.knowledge.retrieval import retrieve_evidence
from sada_bridge.api import create_app
from sada_bridge.policy_claims import PASSAGES
from sada_bridge.policy_grounding import guard_policy_explanation


@pytest.fixture(autouse=True)
def offline():
    with no_network() as attempts:
        yield
    assert not attempts


def evidence():
    return {'schema_version': 'policy_retrieval.v1', 'passages': [
        {k: v for k, v in entry.items() if k != 'claims'} |
        {'passage_id': pid, 'source_verified': True}
        for pid, entry in PASSAGES.items()
    ]}


def core(answer, retrieval=None):
    calls = []
    def provider(*args):
        calls.append(args)
        return answer
    value = explain_policy('Explain the retrieved passage.', retrieval or evidence(),
                           provider=provider, model_id='OFFLINE-BOUNDARY-FIXTURE')
    assert 1 <= len(calls) <= 2
    return value


def accepted_forms():
    return [(pid, form) for pid, entry in PASSAGES.items()
            for claim in entry['claims'].values() for form in claim.values()]


def test_snapshots_match_exact_unchanged_existing_kb_and_retriever():
    kb = json.loads((Path(__file__).parents[1] /
                     'lastmile_ai/knowledge/evidence_chunks.json').read_text())
    byid = {p['evidence_id']: p for p in kb['items']}
    for pid, entry in PASSAGES.items():
        for key in ('text', 'source_id', 'source_title', 'section', 'official_url'):
            assert entry[key] == byid[pid][key]
    for question in ('What does CAP say about the instruction field?',
                     'What does ITU-T Y.3172 describe?'):
        actual = to_policy_retrieval(question, retrieve_evidence(question, top_k=4))
        assert any(p['passage_id'] in PASSAGES and
                   all(p[k] == PASSAGES[p['passage_id']][k] for k in
                       ('text', 'source_id', 'source_title', 'section', 'official_url', 'locator'))
                   for p in actual['passages'])


@pytest.mark.parametrize(('pid', 'form'), accepted_forms())
def test_reviewed_descriptive_forms_are_validation_only(pid, form):
    answer = f'{form} [{pid}].'
    value = core(answer)
    assert value.status == 'Answered'
    out = guard_policy_explanation(value, evidence())
    assert out is value and out.answer == answer
    assert out.llm_invoked is True and out.model_id == 'OFFLINE-BOUNDARY-FIXTURE'


@pytest.mark.parametrize('pid', list(PASSAGES))
@pytest.mark.parametrize(('left', 'right'), [('"', '"'), ("'", "'"), ('“', '”'), ('«', '»')])
def test_complete_original_source_quotes_keep_every_word(pid, left, right):
    answer = left + PASSAGES[pid]['text'] + right + f' [{pid}]'
    assert guard_policy_explanation(core(answer), evidence()).status == 'Answered'


@pytest.mark.parametrize('suffix', [
    ' Therefore this alert is compliant.',
    ' وبالتالي فإن التنبيه سليم نظاميًا.',
    ' except at the other site.',
    ' [SRC-02-E01]',
    '\u200b', ' **Verified**', ' لا بد من إدراجه.',
])
def test_known_fact_never_licenses_unknown_trailing_claims(suffix):
    answer = 'This passage describes the content of the CAP instruction field [SRC-01-E01].' + suffix
    value = core(answer)
    out = guard_policy_explanation(value, evidence())
    assert out.status == 'ReviewRequired' and not out.answer and not out.citations
    assert out.llm_invoked == value.llm_invoked and out.model_id == value.model_id


@pytest.mark.parametrize('key', ['text', 'source_id', 'source_title', 'section', 'official_url', 'locator'])
def test_changed_source_identity_cannot_license_reviewed_prose(key):
    original = evidence()
    value = core('This passage describes the content of the CAP instruction field [SRC-01-E01].')
    changed = copy.deepcopy(original)
    changed['passages'][0][key] += ' changed'
    assert guard_policy_explanation(value, changed).status == 'ReviewRequired'
    assert original == evidence()


@pytest.mark.parametrize('mutate', ['duplicate', 'unverified', 'wrong-citation', 'uncovered', 'empty', 'long'])
def test_ambiguous_or_uncovered_answers_fail_closed(mutate):
    rows = evidence()
    value = core('This passage describes the content of the CAP instruction field [SRC-01-E01].')
    if mutate == 'duplicate':
        rows['passages'].append(copy.deepcopy(rows['passages'][0]))
    elif mutate == 'unverified':
        rows['passages'][0]['source_verified'] = False
    elif mutate == 'wrong-citation':
        value = replace(value, answer=value.answer.replace('SRC-01-E01', 'SRC-02-E01'))
    elif mutate == 'uncovered':
        value = replace(value, answer='Not ' + value.answer)
    elif mutate == 'empty':
        value = replace(value, answer='')
    else:
        value = replace(value, answer=value.answer * 200)
    assert guard_policy_explanation(value, rows).status == 'ReviewRequired'


OLD_UNSAFE = [c for c in load_cases()['cases'] if c['expected'] == 'ReviewRequired']


@pytest.mark.parametrize('case', OLD_UNSAFE, ids=lambda c: c['id'])
def test_every_old_unsafe_holdout_is_now_a_regression(case):
    texts = load_cases()['evidence_sets'][case['source']]
    rows = {'schema_version': 'policy_retrieval.v1', 'passages': [
        {'passage_id': pid, 'source_id': 'HOLDOUT-' + pid,
         'source_title': 'Synthetic holdout', 'section': 'Offline only',
         'text': text, 'official_url': 'https://example.invalid/' + pid,
         'locator': 'Offline only', 'source_verified': True}
        for pid, text in texts.items()
    ]}
    out = guard_policy_explanation(core(case['answer'], rows), rows)
    assert out.status == 'ReviewRequired' and not out.answer and not out.citations


@pytest.mark.parametrize(('question', 'answer', 'expected'), [
    ('What does CAP say about the instruction field?',
     'This passage describes the content of the CAP instruction field [SRC-01-E01].', 'Answered'),
    ('ما معنى حقل instruction في CAP؟',
     'تصف هذه الفقرة محتوى حقل instruction في معيار CAP [SRC-01-E01].', 'Answered'),
    ('What does ITU-T Y.3172 describe?',
     'ITU-T Y.3172 describes a machine-learning architecture for future networks, including IMT-2020 [SRC-02-E01].', 'Answered'),
    ('What does CAP say about the instruction field?',
     'The field is duty-bound to be included [SRC-01-E01].', 'ReviewRequired'),
])
def test_real_website_route_keeps_evidence_and_truthful_transport_metadata(
        tmp_path, monkeypatch, question, answer, expected):
    calls = []
    def provider(prompt, model):
        calls.append((prompt, model))
        return answer
    monkeypatch.setattr('sada_bridge.policy.openrouter_provider', provider)
    with TestClient(create_app(tmp_path / 'offline.sqlite')) as client:
        response = client.post('/api/policy/explain', json={'question': question},
                               headers={'X-SADA-Owner': 'f' * 64})
    result = response.json()
    value = result['explanation']
    assert response.status_code == 200 and len(calls) == 1
    assert value['status'] == expected and value['llm_invoked'] is True
    assert value['model_id'] == 'qwen/qwen-2.5-7b-instruct'
    assert value['execution_mode'] == 'live_llm'  # Offline injected provider, NOT real inference.
    assert value['answer'] == (answer if expected == 'Answered' else '')
    assert result['retrieval']['evidence_items']
    assert 'f' * 64 not in calls[0][0] and 'evaluation_id' not in calls[0][0]
