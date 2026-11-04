"""Offline contract tests for read-only policy explanation sidecar."""
import copy
import unittest
from lastmile_ai.ai.policy_explainer import explain_policy


def retrieval(text='The simulated warning reached 250 residents.'):
    return {'schema_version':'policy_retrieval.v1','query':'What happened?', 'method':'lexical',
            'passages':[{'passage_id':'PASS-01','source_id':'SRC-02','source_title':'Synthetic Test Source',
                         'section':'Test Section','text':text,'official_url':'https://example.org/policy',
                         'locator':'Section 1','source_verified':True}]}


class PolicyExplainerContractTests(unittest.TestCase):
    def test_verified_passage_and_structured_citation(self):
        value=retrieval()
        frozen=copy.deepcopy(value)
        result=explain_policy('What happened?',value,
            provider=lambda p,m:'The simulated warning reached 250 residents. [PASS-01]')
        self.assertEqual(result.status,'Answered')
        self.assertEqual(result.schema_version,'ai_explanation.v1')
        self.assertEqual(result.citations[0]['source_id'],'SRC-02')
        self.assertEqual(result.citations[0]['passage_id'],'PASS-01')
        self.assertEqual(result.execution_mode,'live_llm')
        self.assertTrue(result.llm_invoked)
        self.assertEqual(value,frozen)

    def test_empty_passages_skip_provider(self):
        value=retrieval();value['passages']=[]
        def fail(*_): raise AssertionError('Provider should not be called')
        result=explain_policy('Question',value,provider=fail)
        self.assertEqual(result.status,'InsufficientInformation')
        self.assertFalse(result.llm_invoked)

    def test_unverified_passages_skip_provider(self):
        value=retrieval();value['passages'][0]['source_verified']=False
        result=explain_policy('Question',value,provider=lambda *_:'Surprise')
        self.assertEqual(result.status,'InsufficientInformation')

    def test_model_unavailable(self):
        def broken(*_): raise ConnectionError('Ollama offline')
        result=explain_policy('Question',retrieval(),provider=broken)
        self.assertEqual(result.status,'ModelUnavailable')
        self.assertFalse(result.llm_invoked)
        self.assertIsNone(result.model_id)

    def test_wrong_passage_id_is_rejected(self):
        result=explain_policy('Question',retrieval(),provider=lambda *_:'Answer [FAKE999]')
        self.assertEqual(result.status,'ReviewRequired')

    def test_numeric_claim_unsupported(self):
        result=explain_policy('Question',retrieval(),provider=lambda *_:'The fine is 900000 AED. [PASS-01]')
        self.assertEqual(result.status,'ReviewRequired')

    def test_legal_claim_using_real_number_still_review(self):
        result=explain_policy('Question',retrieval(),provider=lambda *_:'The legal fine is 250 AED. [PASS-01]')
        self.assertEqual(result.status,'ReviewRequired')

    def test_model_says_insufficient(self):
        result=explain_policy('Question',retrieval(),provider=lambda *_:'Insufficient Information — Review Required')
        self.assertEqual(result.status,'InsufficientInformation')
        self.assertTrue(result.llm_invoked)

    def test_question_cannot_be_empty(self):
        with self.assertRaises(ValueError): explain_policy(' ',retrieval())

    def test_unrecognized_schema(self):
        v=retrieval();v['schema_version']='wrong'
        with self.assertRaises(ValueError): explain_policy('Question',v)

    def test_no_unauthorized_links(self):
        result=explain_policy('Question',retrieval(),provider=lambda *_:'Read https://bad.example/source [PASS-01]')
        self.assertEqual(result.status,'ReviewRequired')

    def test_live_prompt_contains_policy_safeguards(self):
        prompts=[]
        def provider(prompt,model):
            prompts.append(prompt)
            return '250 simulated residents received a warning. [PASS-01]'
        explain_policy('Question',retrieval(),provider=provider,scenario_facts={'stage':'T+02:00'})
        self.assertIn('CAP compliant/non-compliant',prompts[0])
        self.assertIn('Never modify simulated results',prompts[0])
        self.assertIn('T+02:00',prompts[0])

if __name__=='__main__': unittest.main()
