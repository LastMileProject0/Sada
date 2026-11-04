"""Offline cross-owner integration tests: real retrieval + mocked LLM."""
import copy
import unittest
from unittest.mock import Mock

from lastmile_ai.ai.maymona_rag_bridge import (
    explain_from_maymona, to_policy_retrieval,
)
from lastmile_ai.knowledge.retrieval import retrieve_evidence


class RagBridgeTests(unittest.TestCase):
    """Test real curated retrieval with a deterministic model stub."""

    def test_cap_question_and_citation(self):
        """Use exact CAP passage ID returned from real retrieval."""
        question = 'هل غياب تعليمات الحماية يعتبر مخالفة لمعيار CAP؟'
        mock = Mock(return_value='The instruction element is optional. [SRC-01-E01]')
        result = explain_from_maymona(question, provider=mock)
        self.assertEqual(result.status, 'Answered')
        self.assertEqual(result.citations[0]['passage_id'], 'SRC-01-E01')
        self.assertEqual(result.citations[0]['source_id'], 'SRC-01')
        self.assertTrue(result.citations[0]['official_url'].startswith('https://'))
        self.assertTrue(result.llm_invoked)  # mocked provider called, not a *real* model smoke test
        self.assertIn('The text describing', mock.call_args.args[0])

    def test_accessibility_source_retrieval(self):
        """Identify the corresponding official accessibility excerpts."""
        q = 'هل سياسة الإتاحة تتناول الطوارئ وذوي الإعاقة؟'
        result = retrieve_evidence(q)
        self.assertEqual(result['status'], 'EVIDENCE_FOUND')
        self.assertTrue(result['evidence_items'])
        self.assertTrue(all(i['source_id'] == 'SRC-04' for i in result['evidence_items']))
        adapted = to_policy_retrieval(q, result)
        self.assertTrue(all(p['source_verified'] for p in adapted['passages']))

    def test_privacy_retrieval_and_conservative_legal_review(self):
        """Flag a legal conclusion even if a valid source ID is cited."""
        q = 'هل مشاركة بيانات الإتاحة مع طرف خارجي مسموحة تلقائيا؟'
        result = retrieve_evidence(q)
        self.assertTrue(result['evidence_items'])
        self.assertTrue(all(i['source_id'] == 'SRC-05' for i in result['evidence_items']))
        citation = result['evidence_items'][0]['evidence_id']
        fake = Mock(return_value=f'This is legally required. [{citation}]')
        response = explain_from_maymona(q, provider=fake)
        self.assertEqual(response.status, 'ReviewRequired')
        self.assertFalse(response.citations)

    def test_unrelated_question_does_not_call_llm(self):
        """Return insufficient information and skip model completely."""
        question = 'ما سعر تذاكر القطار في كيوتو 2042؟'
        fake = Mock(side_effect=AssertionError('LLM must not be called'))
        result = explain_from_maymona(question, provider=fake)
        self.assertEqual(result.status, 'InsufficientInformation')
        self.assertFalse(result.llm_invoked)
        fake.assert_not_called()

    def test_unavailable_provider(self):
        """Return ModelUnavailable instead of fake generated output."""
        fake = Mock(side_effect=ConnectionError('Ollama offline'))
        result = explain_from_maymona('هل غياب تعليمات الحماية يعتبر مخالفة لمعيار CAP؟',provider=fake)
        self.assertEqual(result.status, 'ModelUnavailable')
        self.assertFalse(result.llm_invoked)

    def test_fabricated_citation_rejected(self):
        """Reject a citation to a passage that was not retrieved."""
        fake = Mock(return_value='This is required. [FAKE999]')
        result = explain_from_maymona('هل غياب تعليمات الحماية يعتبر مخالفة لمعيار CAP؟',provider=fake)
        self.assertEqual(result.status, 'ReviewRequired')
        self.assertFalse(result.citations)

    def test_tampered_passage_rejected(self):
        """Never mark modified excerpt text as source-verified."""
        question = 'هل غياب تعليمات الحماية يعتبر مخالفة لمعيار CAP؟'
        result = retrieve_evidence(question)
        broken = copy.deepcopy(result)
        broken['evidence_items'][0]['text'] += ' Made-up rule.'
        with self.assertRaisesRegex(ValueError,'provenance mismatch'):
            to_policy_retrieval(question,broken)

    def test_wrong_source_rejected(self):
        """Reject a changed source ID even if the evidence ID remains valid."""
        question = 'هل غياب تعليمات الحماية يعتبر مخالفة لمعيار CAP؟'
        result = retrieve_evidence(question)
        broken = copy.deepcopy(result)
        broken['evidence_items'][0]['source_id']='SRC-05'
        with self.assertRaisesRegex(ValueError,'provenance mismatch'):
            to_policy_retrieval(question,broken)

    def test_no_mutation_of_retriever_output(self):
        """Keep Maymona's original response read-only."""
        question = 'هل غياب تعليمات الحماية يعتبر مخالفة لمعيار CAP؟'
        data=retrieve_evidence(question)
        original=copy.deepcopy(data)
        to_policy_retrieval(question,data)
        self.assertEqual(data,original)

    def test_unexpected_retrieval_status_rejected(self):
        """Reject inconsistent retriever status instead of guessing."""
        question = 'هل غياب تعليمات الحماية يعتبر مخالفة لمعيار CAP؟'
        data=retrieve_evidence(question)
        data['status']='UNKNOWN'
        with self.assertRaises(ValueError):
            to_policy_retrieval(question,data)


if __name__ == '__main__':
    unittest.main()
