"""Unit tests for Maymona's isolated text-evidence retrieval component."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lastmile_ai.knowledge.retrieval import load_evidence_corpus, retrieve_evidence


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.corpus = load_evidence_corpus()

    def test_five_approved_sources_present(self):
        self.assertEqual({"SRC-01", "SRC-02", "SRC-03", "SRC-04", "SRC-05"}, {i["source_id"] for i in self.corpus["items"]})

    def test_real_text_not_metadata_only(self):
        for item in self.corpus["items"]:
            self.assertGreater(len(item["text"].split()), 7)
            self.assertIn("https://", item["official_url"])
            self.assertTrue(item["section"])

    def test_question_1_cap(self):
        data = retrieve_evidence("Is a missing protective instruction field automatically a CAP 1.2 violation?")
        self.assertEqual("EVIDENCE_FOUND", data["status"])
        self.assertEqual("SRC-01", data["evidence_items"][0]["source_id"])
        self.assertIn("OPTIONAL", data["evidence_items"][0]["text"])

    def test_question_2_accessibility(self):
        data = retrieve_evidence("Does UAE digital accessibility policy support considering alternative alert formats for people who cannot use a voice or visual warning?")
        self.assertEqual("EVIDENCE_FOUND", data["status"])
        self.assertEqual("SRC-04", data["evidence_items"][0]["source_id"])
        self.assertIn("emergency services", data["evidence_items"][0]["text"])

    def test_question_3_privacy(self):
        data = retrieve_evidence("Can a proposed outside emergency-alert partner automatically receive disability-related resident data under UAE personal-data law?")
        self.assertEqual("EVIDENCE_FOUND", data["status"])
        self.assertIn("SRC-05", [e["source_id"] for e in data["evidence_items"]])

    def test_unrelated_sources_are_filtered(self):
        """Check two demo questions are filtered to matching policy sources."""
        accessibility = retrieve_evidence(
            "Does UAE digital accessibility policy support considering "
            "alternative alert formats for people who cannot use a "
            "voice or visual warning?"
        )
        self.assertEqual("EVIDENCE_FOUND", accessibility["status"])
        self.assertTrue(accessibility["evidence_items"])
        self.assertTrue(
            all(item["source_id"] == "SRC-04" for item in accessibility["evidence_items"])
        )

        privacy = retrieve_evidence(
            "Can a proposed outside emergency-alert partner automatically "
            "receive disability-related resident data under UAE "
            "personal-data law?"
        )
        self.assertEqual("EVIDENCE_FOUND", privacy["status"])
        self.assertTrue(privacy["evidence_items"])
        self.assertTrue(
            all(item["source_id"] == "SRC-05" for item in privacy["evidence_items"])
        )

    def test_question_4_no_evidence(self):
        data = retrieve_evidence("What will the train ticket price in Kyoto be on 19 December 2042?")
        self.assertEqual("INSUFFICIENT_EVIDENCE", data["status"])
        self.assertEqual([], data["evidence_items"])

    def test_unsupported_certification_is_not_proven(self):
        data = retrieve_evidence("Did LastMile obtain ISO 27001 certification from the UN in 2026?")
        self.assertEqual("INSUFFICIENT_EVIDENCE", data["status"])

    def test_arabic_cap_question(self):
        data = retrieve_evidence("هل غياب تعليمات الحماية يعتبر مخالفة لمعيار CAP؟")
        self.assertEqual("SRC-01", data["evidence_items"][0]["source_id"])

    def test_arabic_accessibility_question(self):
        data = retrieve_evidence("هل سياسة الإتاحة توفر خدمات الطوارئ لذوي الإعاقة؟")
        self.assertEqual("SRC-04", data["evidence_items"][0]["source_id"])

    def test_arabic_privacy_question(self):
        data = retrieve_evidence("هل مشاركة بيانات الخصوصية مع طرف خارجي تحتاج مراجعة قانون؟")
        self.assertIn("SRC-05", [e["source_id"] for e in data["evidence_items"]])

    def test_retrieved_data_belongs_to_whitelist(self):
        allowed = {(i["evidence_id"], i["source_id"], i["text"], i["official_url"]) for i in self.corpus["items"]}
        for q in ("CAP instruction optional", "accessibility emergency services", "privacy personal data purpose"):
            for e in retrieve_evidence(q)["evidence_items"]:
                self.assertIn((e["evidence_id"], e["source_id"], e["text"], e["official_url"]), allowed)

    def test_top_k_bound(self):
        data = retrieve_evidence("data privacy government scope purpose processing", top_k=1)
        self.assertLessEqual(len(data["evidence_items"]), 1)

    def test_invalid_top_k_rejected(self):
        for value in (0, -1, 21, 2.4, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                retrieve_evidence("CAP instruction", top_k=value)

    def test_duplicate_ids_rejected(self):
        bad = dict(self.corpus)
        bad["items"] = self.corpus["items"] + [self.corpus["items"][0]]
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"dup.json";p.write_text(json.dumps(bad))
            with self.assertRaises(ValueError): load_evidence_corpus(p)

    def test_missing_or_empty_question(self):
        self.assertEqual([], retrieve_evidence("   ")["evidence_items"])


if __name__ == "__main__":
    unittest.main()
