
import unittest

from ai_explanation.ai_explanation import (
    RetrievedEvidence,
    validate_evidence,
    prepare_question,
)


class TestAIExplanation(unittest.TestCase):
    """Test the AI explanation component."""

    def test_valid_evidence(self):
        """Verify that complete evidence passes validation."""
        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Test Reference",
            section="Section 1",
            source_url="https://example.org",
            text="This is a test passage.",
        )

        self.assertTrue(validate_evidence(evidence))

    def test_generate_ai_explanation_with_mock(self):
        """Verify model responses without a live Ollama connection."""
        from unittest.mock import patch, MagicMock
        from ai_explanation.ai_explanation import generate_ai_explanation

        mock_response = MagicMock()
        mock_response.read.return_value = (
            b'{"response": "Accessible warnings save lives."}'
        )

        with patch(
            "ai_explanation.ai_explanation.request.urlopen"
        ) as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value = mock_response

            result = generate_ai_explanation(
                "Why are accessible alerts important?"
            )

        self.assertEqual(
            result,
            "Accessible warnings save lives.",
        )

    def test_missing_evidence_text(self):
        """Verify that evidence without passage text is rejected."""
        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Test Reference",
            section="Section 1",
            source_url="https://example.org",
            text="",
        )

        self.assertFalse(validate_evidence(evidence))

    def test_prepare_question(self):
        """Verify that surrounding whitespace is removed."""
        result = prepare_question(
            "  What makes an emergency warning accessible?  "
        )

        self.assertEqual(
            result,
            "What makes an emergency warning accessible?",
        )

    def test_empty_question(self):
        """Verify that empty questions are rejected."""
        with self.assertRaises(ValueError):
            prepare_question("   ")

    def test_build_evidence_prompt(self):
        """Verify that the prompt includes the question and evidence."""
        from ai_explanation.ai_explanation import build_evidence_prompt

        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Test Reference",
            section="Section 1",
            source_url="https://example.org",
            text="Emergency alerts should be accessible.",
        )

        prompt = build_evidence_prompt(
            "Why is accessibility important?",
            [evidence],
        )

        self.assertIn("Why is accessibility important?", prompt)
        self.assertIn("TEST001", prompt)
        self.assertIn("Emergency alerts should be accessible.", prompt)
        self.assertIn("Insufficient Information", prompt)

    def test_build_prompt_without_evidence(self):
        """Verify that a prompt cannot be built without evidence."""
        from ai_explanation.ai_explanation import build_evidence_prompt

        with self.assertRaises(ValueError):
            build_evidence_prompt(
                "Why is accessibility important?",
                [],
            )

    def test_explain_with_evidence(self):
        """Verify that retrieved evidence is passed to the AI model."""
        from unittest.mock import patch
        from ai_explanation.ai_explanation import explain_with_evidence

        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Test Reference",
            section="Section 1",
            source_url="https://example.org",
            text="Emergency alerts should be accessible.",
        )

        with patch(
            "ai_explanation.ai_explanation.generate_ai_explanation"
        ) as mock_generate:
            mock_generate.return_value = "Explanation [TEST001]"

            result = explain_with_evidence(
                "Why is accessibility important?",
                [evidence],
            )

        self.assertEqual(result, "Explanation [TEST001]")
        mock_generate.assert_called_once()

        prompt = mock_generate.call_args.args[0]
        self.assertIn("TEST001", prompt)
        self.assertIn("Why is accessibility important?", prompt)

    def test_no_evidence_prevents_model_call(self):
        """Verify that missing evidence blocks AI generation."""
        from unittest.mock import patch
        from ai_explanation.ai_explanation import explain_with_evidence

        with patch(
            "ai_explanation.ai_explanation.generate_ai_explanation"
        ) as mock_generate:
            with self.assertRaises(ValueError):
                explain_with_evidence(
                    "What is the legal fine for an alert violation?",
                    [],
                )

            mock_generate.assert_not_called()

    def test_valid_citation(self):
        """Verify that approved source IDs pass citation validation."""
        from ai_explanation.ai_explanation import validate_citations

        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Test Reference",
            section="Section 1",
            source_url="https://example.org",
            text="Emergency warnings should be accessible.",
        )

        explanation = "Accessible alerts are important. [TEST001]"

        self.assertTrue(
            validate_citations(explanation, [evidence])
        )

    def test_invalid_citation(self):
        """Verify that unapproved source IDs are rejected."""
        from ai_explanation.ai_explanation import validate_citations

        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Test Reference",
            section="Section 1",
            source_url="https://example.org",
            text="Emergency warnings should be accessible.",
        )

        explanation = "Accessible alerts are important. [FAKE999]"

        self.assertFalse(
            validate_citations(explanation, [evidence])
        )

    def test_explanation_with_valid_citation(self):
        """Verify that explanations with approved citations pass."""
        from unittest.mock import patch
        from ai_explanation.ai_explanation import explain_with_evidence

        evidence = RetrievedEvidence(
            "TEST001",
            "Test Reference",
            "Section 1",
            "https://example.org",
            "Accessible emergency warnings are important.",
        )

        with patch(
            "ai_explanation.ai_explanation.generate_ai_explanation",
            return_value="Accessible alerts matter. [TEST001]",
        ):
            result = explain_with_evidence(
                "Why is accessibility important?",
                [evidence],
            )

        self.assertEqual(
            result,
            "Accessible alerts matter. [TEST001]",
        )

    def test_explanation_with_invalid_citation(self):
        """Verify that unapproved citations are rejected."""
        from unittest.mock import patch
        from ai_explanation.ai_explanation import explain_with_evidence

        evidence = RetrievedEvidence(
            "TEST001",
            "Test Reference",
            "Section 1",
            "https://example.org",
            "Accessible emergency warnings are important.",
        )

        with patch(
            "ai_explanation.ai_explanation.generate_ai_explanation",
            return_value="Accessible alerts matter. [FAKE999]",
        ):
            result = explain_with_evidence(
                "Why is accessibility important?",
                [evidence],
            )

        self.assertEqual(
            result,
            "Review Required — Invalid or Missing Citations",
        )

    def test_explanation_without_citation(self):
        """Verify that explanations without citations are rejected."""
        from unittest.mock import patch
        from ai_explanation.ai_explanation import explain_with_evidence

        evidence = RetrievedEvidence(
            "TEST001",
            "Test Reference",
            "Section 1",
            "https://example.org",
            "Accessible emergency warnings are important.",
        )

        with patch(
            "ai_explanation.ai_explanation.generate_ai_explanation",
            return_value="Accessible alerts are important.",
        ):
            result = explain_with_evidence(
                "Why is accessibility important?",
                [evidence],
            )

        self.assertEqual(
            result,
            "Review Required — Invalid or Missing Citations",
        )

    def test_explanation_with_mixed_citations(self):
        """Reject explanations containing unapproved citations."""
        from unittest.mock import patch
        from ai_explanation.ai_explanation import explain_with_evidence

        evidence = RetrievedEvidence(
            "TEST001",
            "Test Reference",
            "Section 1",
            "https://example.org",
            "Accessible emergency warnings are important.",
        )

        with patch(
            "ai_explanation.ai_explanation.generate_ai_explanation",
            return_value="Accessible alerts matter. [TEST001] [FAKE999]",
        ):
            result = explain_with_evidence(
                "Why is accessibility important?",
                [evidence],
            )

        self.assertEqual(
            result,
            "Review Required — Invalid or Missing Citations",
        )

    def test_unsupported_legal_claim_not_verified(self):
        """Detect unsupported legal numbers despite valid source IDs."""
        from ai_explanation.ai_explanation import validate_numeric_claims

        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Synthetic Test Reference",
            section="Section 1",
            source_url="https://example.org",
            text="Emergency warnings should be accessible.",
        )

        explanation = "The legal fine is 900000 AED. [TEST001]"

        self.assertFalse(
            validate_numeric_claims(explanation, [evidence])
        )

    def test_unsupported_numeric_claim(self):
        """Reject numeric claims absent from evidence passages."""
        from ai_explanation.ai_explanation import validate_numeric_claims

        evidence = RetrievedEvidence(
            "TEST001",
            "Synthetic Test Reference",
            "Section 1",
            "https://example.org",
            "Emergency warnings should be accessible.",
        )

        explanation = "The legal fine is 900000 AED. [TEST001]"

        self.assertFalse(
            validate_numeric_claims(explanation, [evidence])
        )

    def test_numeric_claim_present_in_evidence(self):
        """Accept numbers appearing in evidence passages."""
        from ai_explanation.ai_explanation import validate_numeric_claims

        evidence = RetrievedEvidence(
            "TEST001",
            "Synthetic Test Reference",
            "Section 1",
            "https://example.org",
            "The simulated warning reached 250 residents.",
        )

        explanation = "The warning reached 250 residents. [TEST001]"

        self.assertTrue(
            validate_numeric_claims(explanation, [evidence])
        )

    def test_reject_unsupported_numeric_explanation(self):
        """Reject AI explanations containing unsupported numbers."""
        from unittest.mock import patch
        from ai_explanation.ai_explanation import explain_with_evidence

        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Synthetic Test Reference",
            section="Section 1",
            source_url="https://example.org",
            text="Emergency warnings should be accessible.",
        )

        with patch(
            "ai_explanation.ai_explanation.generate_ai_explanation",
            return_value="The legal fine is 900000 AED. [TEST001]",
        ):
            result = explain_with_evidence(
                "What is the legal fine?",
                [evidence],
            )

        self.assertEqual(
            result,
            "Review Required — Unsupported Numeric Claims",
        )

    def test_hearing_accessibility_misrecommendation(self):
        """Flag unsupported voice-only recommendations for review."""
        from unittest.mock import patch
        from ai_explanation.ai_explanation import explain_with_evidence

        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Synthetic Accessibility Test",
            section="Hearing Accessibility",
            source_url="https://example.org",
            text=(
                "This simulated resident cannot use voice-only alerts. "
                "Accessible text or visual alternatives are required."
            ),
        )

        with patch(
            "ai_explanation.ai_explanation.generate_ai_explanation",
            return_value=(
                "Voice-only calls are recommended for this resident. "
                "[TEST001]"
            ),
        ):
            result = explain_with_evidence(
                "Which alert channel is suitable for this resident?",
                [evidence],
            )

        self.assertEqual(
            result,
            "Review Required — Unsupported Accessibility Claim",
        )

    def test_numeric_claim_wrong_context(self):
        """Show that numeric matching cannot verify claim context."""
        from ai_explanation.ai_explanation import validate_numeric_claims

        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Synthetic Test Reference",
            section="Simulation Results",
            source_url="https://example.org",
            text="The simulated warning reached 250 residents.",
        )

        explanation = "The legal fine is 250 AED. [TEST001]"

        self.assertTrue(
            validate_numeric_claims(explanation, [evidence])
        )

    def test_legal_claim_requires_review(self):
        """Flag legal claims even when citations and numbers are valid."""
        from unittest.mock import patch
        from ai_explanation.ai_explanation import explain_with_evidence

        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Synthetic Test Reference",
            section="Simulation Results",
            source_url="https://example.org",
            text="The simulated warning reached 250 residents.",
        )

        with patch(
            "ai_explanation.ai_explanation.generate_ai_explanation",
            return_value="The legal fine is 250 AED. [TEST001]",
        ):
            result = explain_with_evidence(
                "What is the legal fine?",
                [evidence],
            )

        self.assertEqual(
            result,
            "Review Required — Legal Claim",
        )
    
    def test_visual_accessibility_misrecommendation(self):
        """
        Flag signage recommendations that contradict visual evidence.
        """
        from unittest.mock import patch
        from ai_explanation.ai_explanation import explain_with_evidence

        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Synthetic Accessibility Test",
            section="Visual Accessibility",
            source_url="https://example.org",
            text=(
                "This simulated resident cannot read digital signage. "
                "Digital signage alone is not suitable for this resident."
            ),
        )

        with patch(
            "ai_explanation.ai_explanation.generate_ai_explanation",
            return_value=(
                "Digital signage alone is recommended for this resident. "
                "[TEST001]"
            ),
        ):
            result = explain_with_evidence(
                "Which warning channel is suitable for this resident?",
                [evidence],
            )

        self.assertEqual(
            result,
            "Review Required — Unsupported Accessibility Claim",
        )
    
    def test_unknown_accessibility_requires_review(self):
        """
        Require review when accessibility suitability is unknown.
        """
        from unittest.mock import patch
        from ai_explanation.ai_explanation import explain_with_evidence

        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Synthetic Accessibility Test",
            section="Accessibility Status",
            source_url="https://example.org",
            text=(
                "Voice usability for this simulated resident "
                "is Unknown. No suitability decision is available."
            ),
        )

        with patch(
            "ai_explanation.ai_explanation.generate_ai_explanation",
            return_value=(
                "Voice calls are definitely suitable for this resident. "
                "[TEST001]"
            ),
        ):
            result = explain_with_evidence(
                "Is the voice channel suitable for this resident?",
                [evidence],
            )

        self.assertEqual(
            result,
            "Review Required — Unknown Accessibility Status",
        )
    
    def test_arabic_hearing_accessibility_misrecommendation(self):
        """
        Flag Arabic voice-only recommendations that contradict evidence.
        """
        from unittest.mock import patch
        from ai_explanation.ai_explanation import explain_with_evidence

        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Synthetic Accessibility Test",
            section="Hearing Accessibility",
            source_url="https://example.org",
            text=(
                "هذا المقيم لا يستطيع استخدام التحذيرات الصوتية فقط. "
                "يحتاج إلى بديل نصي مناسب."
            ),
        )

        with patch(
            "ai_explanation.ai_explanation.generate_ai_explanation",
            return_value=(
                "نوصي باستخدام المكالمات الصوتية فقط لهذا المقيم. "
                "[TEST001]"
            ),
        ):
            result = explain_with_evidence(
                "ما قناة التحذير المناسبة لهذا المقيم؟",
                [evidence],
            )

        self.assertEqual(
            result,
            "Review Required — Unsupported Accessibility Claim",
        )
    
    def test_ai_explanation_does_not_modify_evidence(self):
        """
        Keep retrieved evidence unchanged during AI explanation.
        """
        from unittest.mock import patch
        from ai_explanation.ai_explanation import explain_with_evidence

        evidence = RetrievedEvidence(
            source_id="TEST001",
            source_title="Synthetic Test Reference",
            section="Simulation Results",
            source_url="https://example.org",
            text="The simulated warning reached 250 residents.",
        )

        evidence_items = [evidence]
        original_items = evidence_items.copy()

        with patch(
            "ai_explanation.ai_explanation.generate_ai_explanation",
            return_value="The warning reached 250 residents. [TEST001]",
        ):
            explain_with_evidence(
                "How many residents received the warning?",
                evidence_items,
            )

        self.assertEqual(evidence_items, original_items)
        self.assertEqual(evidence.text, original_items[0].text)

if __name__ == "__main__":
    unittest.main()
