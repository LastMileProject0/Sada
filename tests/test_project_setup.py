"""Tests owned by Sirin: scaffold only, not simulated delivery validation."""
import unittest
from lastmile_ai.__main__ import verify_setup


class TestProjectBootstrap(unittest.TestCase):
    def test_approved_basics_and_source_presence(self):
        data = verify_setup()
        self.assertEqual(data["synthetic_residents"], 1000)
        self.assertEqual(data["max_recovery_candidates"], 3)
        self.assertEqual(len(data["channels"]), 5)

    def test_stage_selection_cannot_use_outage_end(self):
        stages = verify_setup()["selectable_stages"]
        self.assertEqual(stages, ["T+00:00", "T+02:00", "T+04:00", "T+06:00"])
        self.assertNotIn("T+07:00", stages)


if __name__ == "__main__":
    unittest.main()
