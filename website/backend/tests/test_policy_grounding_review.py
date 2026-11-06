"""Offline regressions for the approved website-only acceptance guard.

REQUIRED/RECOMMENDED comparison sources below are synthetic UNIT FIXTURES, not
additions to the approved KB and not assertions about any real standard.
"""
import itertools
import copy
from dataclasses import replace
from urllib import request

import pytest
from fastapi.testclient import TestClient

from lastmile_ai.ai.maymona_rag_bridge import to_policy_retrieval
from lastmile_ai.ai.policy_explainer import explain_policy
from lastmile_ai.knowledge.retrieval import retrieve_evidence
from sada_bridge.policy_grounding import guard_policy_explanation
from sada_bridge.api import create_app

QUESTION = 'What does CAP say about the instruction field?'
PID = 'SRC-01-E01'
OBSERVED_ENGLISH = (
    'The Common Alerting Protocol (CAP) Version 1.2 recommends including an '
    'instruction field that describes the recommended action to be taken by '
    'recipients of the alert message. This field is considered optional [SRC-01-E01].'
)


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Network is forbidden in this offline grounding review')
    monkeypatch.setattr(request, 'urlopen', forbidden)
    monkeypatch.setattr(request.OpenerDirector, 'open', forbidden)


@pytest.fixture
def cap():
    return to_policy_retrieval(QUESTION, retrieve_evidence(QUESTION, top_k=4))


def run_offline(evidence, answer):
    calls = []

    def fixture_provider(prompt, model):
        calls.append(prompt)
        return answer

    result = explain_policy(QUESTION, evidence, provider=fixture_provider,
                            model_id='OFFLINE-UNIT-FIXTURE')
    assert len(calls) == 1, 'All fixtures have existing valid citation IDs'
    return guard_policy_explanation(result, evidence)


@pytest.mark.parametrize('answer', [
    'The instruction field is optional and describes the recommended action '
    'for recipients [SRC-01-E01].',
    'حقل instruction اختياري ويصف الإجراء الموصى به لمتلقي التنبيه [SRC-01-E01].',
    'Including the instruction field is not required [SRC-01-E01].',
    'حقل instruction اختياري وليس إلزاميًا [SRC-01-E01].',
])
def test_unquoted_normative_paraphrases_now_require_review(cap, answer):
    assert run_offline(cap, answer).status == 'ReviewRequired'


@pytest.mark.parametrize('answer', [
    OBSERVED_ENGLISH,
    'Including the instruction field is required [SRC-01-E01].',
    'The instruction field must be included [SRC-01-E01].',
    'The instruction field should be included [SRC-01-E01].',
    'يوصى بإدراج حقل instruction في التنبيه [SRC-01-E01].',
    'يجب إدراج حقل instruction في التنبيه [SRC-01-E01].',
    'ينبغي إدراج حقل instruction في التنبيه [SRC-01-E01].',
    'يتعين إدراج حقل instruction في التنبيه [SRC-01-E01].',
])
def test_optional_cannot_be_upgraded_to_inclusion_recommendation_or_requirement(cap, answer):
    assert run_offline(cap, answer).status == 'ReviewRequired'


MODALITY = {
    'en': {
        'OPTIONAL': 'The TEST field is OPTIONAL.',
        'REQUIRED': 'The TEST field is REQUIRED.',
        'RECOMMENDED': 'The TEST field is RECOMMENDED.',
    },
    'ar': {
        'OPTIONAL': 'الحقل التجريبي اختياري.',
        'REQUIRED': 'الحقل التجريبي إلزامي.',
        'RECOMMENDED': 'الحقل التجريبي موصى به.',
    },
}


def synthetic_evidence(text, passage_id='UNIT-MODALITY'):
    # Deliberate contract fixture like existing core tests, bypassing corpus
    # provenance conversion. Never presented as approved real-world evidence.
    return {
        'schema_version': 'policy_retrieval.v1',
        'passages': [{
            'passage_id': passage_id, 'source_id': 'OFFLINE-TEST-SOURCE',
            'source_title': 'Synthetic UNIT fixture, not approved KB',
            'section': 'Offline comparison only', 'text': text,
            'official_url': 'https://example.org/offline-unit-fixture',
            'locator': 'Offline comparison only', 'source_verified': True,
        }],
    }


@pytest.mark.parametrize('language', ['en', 'ar'])
@pytest.mark.parametrize('modality', ['OPTIONAL', 'REQUIRED', 'RECOMMENDED'])
def test_synthetic_source_quotes_cannot_expand_the_two_passage_scope(language, modality):
    sentence = MODALITY[language][modality]
    answer = f'"{sentence}" [UNIT-MODALITY]'
    assert run_offline(synthetic_evidence(sentence), answer).status == 'ReviewRequired'


@pytest.mark.parametrize('language', ['en', 'ar'])
@pytest.mark.parametrize(('source_modality', 'claimed_modality'),
                         list(itertools.permutations(MODALITY['en'], 2)))
def test_source_modality_must_not_be_relabelled(language, source_modality, claimed_modality):
    evidence = synthetic_evidence(MODALITY[language][source_modality])
    answer = MODALITY[language][claimed_modality] + ' [UNIT-MODALITY]'
    assert run_offline(evidence, answer).status == 'ReviewRequired'


@pytest.mark.parametrize('answer', [
    'This alert is CAP compliant [SRC-01-E01].',
    'This alert meets all legal requirements [SRC-01-E01].',
    'هذا التنبيه متوافق مع معيار CAP [SRC-01-E01].',
    'هذا التنبيه مستوفٍ للمتطلبات القانونية [SRC-01-E01].',
])
def test_compliance_and_legal_conclusions_require_review_even_with_valid_citation(cap, answer):
    assert run_offline(cap, answer).status == 'ReviewRequired'


@pytest.mark.parametrize('answer', [
    'The instruction field is legally required [SRC-01-E01].',
    'حقل instruction ملزم قانونيًا [SRC-01-E01].',
])
def test_existing_selected_legal_patterns_already_require_review(cap, answer):
    assert run_offline(cap, answer).status == 'ReviewRequired'


@pytest.mark.parametrize('answer', [
    'This excerpt does not establish CAP compliance [SRC-01-E01].',
    'لا تثبت هذه الفقرة امتثال التنبيه لمعيار CAP [SRC-01-E01].',
])
def test_unreviewed_noncertification_wording_is_not_an_implicit_exception(cap, answer):
    assert run_offline(cap, answer).status == 'ReviewRequired'


@pytest.mark.parametrize(('other_source', 'answer'), [
    ('The EXIT field is REQUIRED.',
     'The TEST field is REQUIRED [UNIT-MODALITY] [UNIT-OTHER].'),
    ('حقل EXIT إلزامي.',
     'الحقل التجريبي إلزامي [UNIT-MODALITY] [UNIT-OTHER].'),
])
def test_unrelated_cited_subject_cannot_supply_requirement(other_source, answer):
    evidence = synthetic_evidence('The TEST field is OPTIONAL.')
    evidence['passages'].extend(synthetic_evidence(other_source, 'UNIT-OTHER')['passages'])
    assert run_offline(evidence, answer).status == 'ReviewRequired'


@pytest.mark.parametrize('answer', [
    '"REQUIRED" [UNIT-MODALITY]',
    '"The TEST field is REQUIRED." [UNIT-OTHER]',
    'For the EXIT field: "The TEST field is REQUIRED." [UNIT-MODALITY]',
    'Not "The TEST field is REQUIRED." [UNIT-MODALITY]',
    '"The TEST field is REQUIRED." [unit-modality]',
    '"The TEST field is REQUIRED." [UNIT-MODALITY] but optional [UNIT-MODALITY]',
])
def test_partial_quotes_wrong_citations_and_subject_reframing_are_withheld(answer):
    evidence = synthetic_evidence('The TEST field is REQUIRED.')
    evidence['passages'].extend(synthetic_evidence('The EXIT field is REQUIRED.', 'UNIT-OTHER')['passages'])
    # Exercise the gate directly: original invalid-ID handling may already
    # reject the lowercase-ID fixture before this additional check.
    base = explain_policy(QUESTION, evidence,
                          provider=lambda *_: '"The TEST field is REQUIRED." [UNIT-MODALITY]',
                          model_id='OFFLINE-UNIT-FIXTURE')
    result = guard_policy_explanation(replace(base, answer=answer), evidence)
    assert result.status == 'ReviewRequired' and not result.answer and not result.citations


@pytest.mark.parametrize('quotes', [('“', '”'), ('«', '»')])
def test_exact_whole_clause_source_quotes_with_unicode_quote_marks(quotes):
    text = 'الحقل التجريبي إلزامي.'
    answer = f'{quotes[0]}{text}{quotes[1]} [UNIT-MODALITY]'
    assert run_offline(synthetic_evidence(text), answer).status == 'ReviewRequired'


@pytest.mark.parametrize('answer', [
    'يُوصَى بِإِدْرَاجِ حَقْلِ instruction [SRC-01-E01].',
    'إدراج حقل instruction إِلْزَامِيّ [SRC-01-E01].',
    'Including the instruction field is prohibited [SRC-01-E01].',
    'CAP advises including the instruction field [SRC-01-E01].',
    'The field is re\u200bquired [SRC-01-E01].',
    'This excerpt does not establish CAP compliance, but this alert is compliant [SRC-01-E01].',
    'لا تثبت هذه الفقرة امتثال التنبيه لمعيار CAP لكن التنبيه متوافق [SRC-01-E01].',
])
def test_normalization_prohibitions_and_mixed_disclaimer_verdicts(cap, answer):
    assert run_offline(cap, answer).status == 'ReviewRequired'


def test_citation_after_sentence_punctuation_stays_with_source_clause(cap):
    assert run_offline(cap, 'This passage describes the content of the CAP instruction field. [SRC-01-E01]').status == 'Answered'


@pytest.mark.parametrize('text', [
    'When condition X holds; the TEST field is REQUIRED.',
    'Except in condition X, the TEST field is REQUIRED.',
    'The TEST field is not REQUIRED.',
])
def test_quotes_cannot_omit_source_conditions_or_negation(text):
    result = run_offline(synthetic_evidence(text),
                         '"The TEST field is REQUIRED." [UNIT-MODALITY]')
    assert result.status == 'ReviewRequired'


def test_rejection_preserves_real_invocation_and_inputs_without_rewriting(cap):
    frozen = copy.deepcopy(cap)
    base = explain_policy(QUESTION, cap, provider=lambda *_: OBSERVED_ENGLISH,
                          model_id='OFFLINE-UNIT-FIXTURE')
    assert base.status == 'Answered'  # Original core deliberately unchanged.
    result = guard_policy_explanation(base, cap)
    assert result.status == 'ReviewRequired' and not result.answer and not result.citations
    assert result.llm_invoked == base.llm_invoked is True
    assert result.model_id == base.model_id and result.execution_mode == 'live_llm'
    assert result.question == base.question and cap == frozen
    assert base.answer == OBSERVED_ENGLISH  # Frozen original was not modified.
    assert result.limitations[:-1] == base.limitations


@pytest.mark.parametrize('status', ['ModelUnavailable', 'InsufficientInformation', 'ReviewRequired'])
def test_nonanswered_states_are_returned_unchanged(cap, status):
    base = run_offline(cap, 'The instruction field is optional [SRC-01-E01].')
    value = replace(base, status=status, answer='', citations=())
    assert guard_policy_explanation(value, cap) is value


def test_actual_website_router_withholds_saved_bad_answer_but_keeps_evidence(tmp_path, monkeypatch):
    calls = []

    def offline_provider(prompt, model):
        calls.append(prompt)
        return OBSERVED_ENGLISH

    monkeypatch.setattr('sada_bridge.policy.openrouter_provider', offline_provider)
    with TestClient(create_app(tmp_path / 'offline.sqlite')) as client:
        response = client.post('/api/policy/explain', json={'question': QUESTION},
                               headers={'X-SADA-Owner': 'e' * 64})
    data = response.json()
    assert response.status_code == 200 and len(calls) == 1
    assert data['explanation']['status'] == 'ReviewRequired'
    assert data['explanation']['llm_invoked'] is True
    assert data['explanation']['model_id'] == 'qwen/qwen-2.5-7b-instruct'
    assert data['explanation']['answer'] == '' and data['explanation']['citations'] == []
    assert data['retrieval']['evidence_items'][0]['evidence_id'] == PID
    assert 'e' * 64 not in calls[0]
