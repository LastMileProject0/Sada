"""Step 4 Demo Runner: validated planner choices and real output smoke test."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from demo.run_demo import main, make_configuration
from lastmile_ai.schemas import ChannelID, EventStage


class Step4DemoTests(unittest.TestCase):
    def test_all_stages_and_default_channels(self):
        for stage, enum in (
            ("T+00", EventStage.T00),
            ("T+02", EventStage.T02),
            ("T+04", EventStage.T04),
            ("T+06", EventStage.T06),
        ):
            with self.subTest(stage=stage):
                config = make_configuration(stage)
                self.assertEqual(config.selected_stage, enum)
                self.assertEqual(set(config.enabled_channels), set(ChannelID))

    def test_channels_can_be_enabled_or_disabled(self):
        config = make_configuration(
            "T+02", channels=["CH01", "CH03", "CH05"], disabled=["CH05"]
        )
        self.assertEqual(config.enabled_channels, (ChannelID.SMS, ChannelID.VOICE_CALL))

    def test_reject_zero_channels(self):
        with self.assertRaises(ValueError):
            make_configuration("T+02", channels=[])
        with self.assertRaises(ValueError):
            make_configuration("T+02", disabled=["CH01", "CH02", "CH03", "CH04", "CH05"])

    def test_reject_invalid_stage_and_channel(self):
        with self.assertRaises(ValueError):
            make_configuration("T+07")
        with self.assertRaises(ValueError):
            make_configuration("T+02", channels=["CH06"])
        with self.assertRaises(ValueError):
            make_configuration("T+02", channels=["CH01", "CH01"])

    def test_real_run_creates_html_and_markdown(self):
        # Run the actual approved 1,000-resident integrated pipeline, with no mock data.
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with contextlib.redirect_stdout(io.StringIO()) as captured:
                code = main(["--stage", "T+02", "--output-dir", str(output)])
            self.assertEqual(code, 0)
            html = output / "dashboard.html"
            markdown = output / "report.md"
            self.assertTrue(html.is_file())
            self.assertTrue(markdown.is_file())
            html_text = html.read_text(encoding="utf-8")
            report_text = markdown.read_text(encoding="utf-8")
            self.assertIn("<html", html_text.lower())
            self.assertIn("Before vs After Results", report_text)
            self.assertIn("T+02:00", report_text)
            self.assertIn("recommended plan:", captured.getvalue().lower())
            self.assertIn("P0", report_text)


if __name__ == "__main__":
    unittest.main()
