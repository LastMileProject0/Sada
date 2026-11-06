import unittest
from lastmile_ai.report import build_report
from lastmile_ai.dashboard import build_dashboard
from lastmile_ai.schemas import PlanMetrics, Agent4Output, RecoveryOutcome, RecoveryCandidate, PolicyCheckStatus

class ReportingTests(unittest.TestCase):
    def test_no_suitable_recovery_is_not_fabricated(self):
        p0 = PlanMetrics('P0', 300, 200, 80, 350, 0)
        result = Agent4Output(RecoveryOutcome.NO_SUITABLE_PLAN, 'P0', p0, (), p0,
                              'No feasible alternative', ('Privacy review pending',))
        report = build_report(result)
        dashboard = build_dashboard(result)
        self.assertIn('No feasible alternative', report)
        self.assertIn('0.0 percentage points', report)
        self.assertIn('0.0 percentage points', dashboard)
        self.assertIn('Privacy review pending', report)
        self.assertNotIn('740', dashboard)

    def test_rejects_wrong_type(self):
        with self.assertRaises(TypeError):
            build_report({})
        with self.assertRaises(TypeError):
            build_dashboard({})

if __name__ == '__main__':
    unittest.main()
