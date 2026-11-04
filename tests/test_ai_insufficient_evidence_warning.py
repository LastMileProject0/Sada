"""Regression test for a mid-answer insufficient-evidence warning."""
import unittest
from lastmile_ai.ai.policy_explainer import explain_policy


class InsufficientEvidenceWarningTests(unittest.TestCase):
    def test_mixed_answer_cannot_be_approved(self):
        q = 'Does the policy discuss accessibility?'
        retrieval = {
            'schema_version': 'policy_retrieval.v1',
            'query': q,
            'method': 'lexical',
            'passages': [{
                'passage_id': 'SRC-04-E01',
                'source_id': 'SRC-04',
                'source_title': 'UAE National Policy for Digital Accessibility',
                'section': 'Article (2), Policy Objective',
                'text': 'Digital Accessibility technologies enable People of Determination to use services, including emergency services.',
                'official_url': 'https://example.org/policy',
                'locator': 'PDF page 6; Article (2)',
                'source_verified': True,
            }],
        }
        result = explain_policy(
            q, retrieval,
            provider=lambda prompt, model: (
                'The policy discusses accessibility [SRC-04-E01]. '
                '[INSUFFICIENT INFORMATION - REVIEW REQUIRED]'
            ),
        )
        self.assertEqual('ReviewRequired', result.status)
        self.assertTrue(result.llm_invoked)
        self.assertEqual('', result.answer)


if __name__ == '__main__':
    unittest.main()
