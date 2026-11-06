"""Smoke-check Ethar-aware dashboard/report generation independently of old demo."""
import tempfile
import unittest
from pathlib import Path
from demo.run_ethar_stage_demo import main


class EtharStageDemoTests(unittest.TestCase):
    def test_t04_dashboard_and_report_generated(self):
        """Render real T+04 EV02 results without editing legacy demo."""
        with tempfile.TemporaryDirectory() as temp:
            code = main(['--stage', 'T+04', '--output-dir', temp])
            self.assertEqual(code, 0)
            dashboard = Path(temp) / 'dashboard.html'
            report = Path(temp) / 'report.md'
            self.assertTrue(dashboard.is_file())
            self.assertTrue(report.is_file())
            self.assertIn('P3', report.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
