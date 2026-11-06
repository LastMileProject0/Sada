"""Offline diagnosis: returned evidence is not necessarily approved answer scope.

Providers below are mocks, never real inference. No acceptance rules are changed.
"""
import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from holdout.run_policy_grounding import no_network
from lastmile_ai.ai.maymona_rag_bridge import to_policy_retrieval
from lastmile_ai.ai.policy_explainer import explain_policy
from lastmile_ai.knowledge.retrieval import retrieve_evidence
from sada_bridge.api import create_app
from sada_bridge.openrouter_provider import MODEL, ProviderUnavailable
from sada_bridge.policy_claims import PASSAGES
from sada_bridge.policy_grounding import guard_policy_explanation

KB = Path(__file__).parents[1] / 'lastmile_ai/knowledge/evidence_chunks.json'
QUESTIONS = ['Explain the displayed passage.', 'اشرح الفقرة المعروضة.']


@pytest.fixture(autouse=True)
def offline():
    with no_network() as attempts:
        yield
    assert not attempts


def source_result(question, pid='SRC-04-E01'):
    item = next(row for row in json.loads(KB.read_text())['items']
                if row['evidence_id'] == pid)
    return {'question': question, 'status': 'EVIDENCE_FOUND',
            'evidence_items': [copy.deepcopy(item)], 'limitations': []}


def quote_result(question):
    found = source_result(question)
    rows = to_policy_retrieval(question, found)
    answer = '"' + rows['passages'][0]['text'] + '" [SRC-04-E01]'
    calls = []

    def provider(prompt, model):
        calls.append(model)
        return answer

    core = explain_policy(question, rows, provider=provider, model_id=MODEL)
    return found, rows, core, calls


def test_real_retriever_can_find_source_outside_answer_acceptance_scope():
    found = retrieve_evidence(
        'UAE National Policy for Digital Accessibility People of Determination emergency services',
        top_k=4)
    assert found['status'] == 'EVIDENCE_FOUND'
    assert any(row['evidence_id'] == 'SRC-04-E01' for row in found['evidence_items'])
    assert 'SRC-04-E01' not in PASSAGES
    assert set(PASSAGES) == {'SRC-01-E01', 'SRC-02-E01'}


@pytest.mark.parametrize('question', QUESTIONS)
def test_valid_uae_quote_passes_core_but_not_reviewed_website_scope(question):
    found, rows, core, calls = quote_result(question)
    assert calls == [MODEL]  # Mock transport; proves one call in this test only.
    assert core.status == 'Answered' and core.citations
    before = core.to_dict()
    guarded = guard_policy_explanation(core, rows)
    assert core.to_dict() == before
    assert guarded.status == 'ReviewRequired'
    assert guarded.answer == '' and guarded.citations == ()
    assert guarded.llm_invoked and guarded.execution_mode == 'live_llm'
    assert guarded.model_id == MODEL
    assert 'outside the reviewed demonstration scope' in guarded.limitations[-1]
    assert found['evidence_items'][0]['evidence_id'] == 'SRC-04-E01'


@pytest.mark.parametrize('question', QUESTIONS)
def test_route_preserves_evidence_and_metadata_while_withholding_uae_answer(
        question, tmp_path, monkeypatch):
    found = source_result(question)
    frozen = copy.deepcopy(found)
    answer = '"' + found['evidence_items'][0]['text'] + '" [SRC-04-E01]'
    calls = []

    def provider(prompt, model):
        calls.append((prompt, model))
        return answer

    monkeypatch.setattr('sada_bridge.policy.retrieve_evidence', lambda *a, **k: found)
    monkeypatch.setattr('sada_bridge.policy.openrouter_provider', provider)
    with TestClient(create_app(tmp_path / 'isolated.sqlite')) as client:
        response = client.post('/api/policy/explain', json={'question': question},
                               headers={'X-SADA-Owner': 'c' * 64})
    assert response.status_code == 200 and len(calls) == 1
    result = response.json()
    assert result['retrieval'] == frozen
    explanation = result['explanation']
    assert explanation['status'] == 'ReviewRequired'
    assert explanation['answer'] == '' and explanation['citations'] == []
    assert explanation['llm_invoked'] is True
    assert explanation['execution_mode'] == 'live_llm'
    assert explanation['model_id'] == MODEL
    assert 'c' * 64 not in calls[0][0]


@pytest.mark.parametrize('language', ['en', 'ar'])
def test_in_scope_descriptions_still_pass_without_rewriting(language):
    question = 'Explain the displayed passage.'
    rows = to_policy_retrieval(question, source_result(question, 'SRC-01-E01'))
    form = PASSAGES['SRC-01-E01']['claims']['cap.content'][language]
    answer = form + ' [SRC-01-E01].'
    core = explain_policy(question, rows, provider=lambda *a: answer, model_id=MODEL)
    assert core.status == 'Answered'
    guarded = guard_policy_explanation(core, rows)
    assert guarded is core and guarded.answer == answer


def test_first_provider_failure_has_different_invocation_metadata():
    question = 'Explain the displayed passage.'
    rows = to_policy_retrieval(question, source_result(question))

    def failed_provider(*args):
        raise ProviderUnavailable('Synthetic offline failure')

    core = explain_policy(question, rows, provider=failed_provider, model_id=MODEL)
    assert core.status == 'ModelUnavailable'
    assert core.llm_invoked is False and core.execution_mode == 'fallback'
    assert guard_policy_explanation(core, rows) is core


def test_citation_repair_failure_after_success_can_keep_invoked_true():
    question = 'Explain the displayed passage.'
    rows = to_policy_retrieval(question, source_result(question))
    calls = []

    def provider(*args):
        calls.append(args)
        if len(calls) == 1:
            return 'A synthetic draft without a source tag.'
        raise ProviderUnavailable('Synthetic offline repair failure')

    core = explain_policy(question, rows, provider=provider, model_id=MODEL)
    assert len(calls) == 2
    assert core.status == 'ReviewRequired' and core.llm_invoked
    assert core.answer == '' and core.citations == ()
    assert core.limitations == ('Missing or unrecognized passage citation after strict retry.',)
    assert guard_policy_explanation(core, rows) is core


def test_core_validation_and_website_scope_share_the_reported_metadata():
    question = 'Explain the displayed passage.'
    _, rows, valid, _ = quote_result(question)
    scope_rejected = guard_policy_explanation(valid, rows)
    invalid = explain_policy(
        question, rows, model_id=MODEL,
        provider=lambda *a: 'See https://example.invalid/unverified [SRC-04-E01].')
    assert invalid.status == 'ReviewRequired'
    assert invalid.limitations == ('Unverified URL appeared in generated answer.',)
    assert guard_policy_explanation(invalid, rows) is invalid
    keys = ('status', 'answer', 'citations', 'llm_invoked', 'execution_mode', 'model_id')
    assert {k: invalid.to_dict()[k] for k in keys} == {
        k: scope_rejected.to_dict()[k] for k in keys}
    assert invalid.limitations != scope_rejected.limitations
