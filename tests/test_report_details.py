"""FR-06 report detail checks using actual fixed synthetic data."""
import unittest

from lastmile_ai.report import build_report
from lastmile_ai.recovery_runtime import run_integrated_recovery
from lastmile_ai.schemas import (
    Agent4Output, ChannelID, EventStage, PlanMetrics,
    RecoveryOutcome, SimulationConfiguration,
)


class ReportDetailsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recovery_run = run_integrated_recovery(SimulationConfiguration(EventStage.T02, tuple(ChannelID)))
        cls.report = build_report(cls.recovery_run)

    def test_fr06_five_sections(self):
        for heading in ('## 1. Simulation Overview', '## 2. Before vs After Results',
                        '## 3. Tested Recovery Plans', '## 4. Accessibility & Policy Findings',
                        '## 5. Final Recommendation & Explanation'):
            self.assertIn(heading, self.report)

    def test_actual_results_and_audit_records(self):
        for token in ('722', '942', '366', 'P0 (baseline)', 'P1', 'P2', 'P3',
                      'Hearing impairment', 'Before gaps', 'After review',
                      'CH01 SMS', 'CH05 Digital Signage', 'Authorization',
                      'Privacy', 'CAP advisory'):
            self.assertIn(token, self.report)
        self.assertIn('No Eligible Channel assignments', self.report)
        self.assertNotIn('NOT IMPLEMENTED YET', self.report)

    def test_stated_scope_and_no_pseudo_certification(self):
        self.assertIn('Synthetic pre-event planning only', self.report)
        self.assertIn('No CAP pass/fail or legal compliance certification', self.report)
        self.assertIn('Sirens are alert-only', self.report)
        self.assertIn('Potential evaluations are excluded', self.report)
        self.assertNotIn('100% legal compliance', self.report)

    def test_summary_only_backwards_compatible(self):
        p0 = PlanMetrics('P0', 300, 200, 80, 350, 0)
        summary = Agent4Output(RecoveryOutcome.NO_SUITABLE_PLAN, 'P0', p0, (),
                               p0, 'No feasible alternative', ('Review pending',))
        doc = build_report(summary)
        self.assertIn('0.0 percentage points', doc)
        self.assertIn('No feasible alternative', doc)
        self.assertIn('Review pending', doc)
        self.assertIn('Not supplied', doc)
        self.assertIn('retain P0', doc)
        with self.assertRaises(TypeError):
            build_report({})

    def test_traceability_and_markdown_format(self):
        self.assertIn('SCENARIO_AUTH', self.report)
        self.assertTrue(self.report.endswith('\n'))


if __name__ == '__main__':
    unittest.main()
