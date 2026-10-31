"""Step 4 Salma: reproducible comparison and decision-audit tests."""
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from analysis.step4_compare_plans import comparison_rows, main, render_markdown
from lastmile_ai.recovery_runtime import run_integrated_recovery
from lastmile_ai.schemas import ChannelID, EventStage, SimulationConfiguration


class PlanComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = SimulationConfiguration(EventStage.T00, tuple(ChannelID))
        cls.recovery_result = run_integrated_recovery(cls.config)

    def test_all_real_plans_and_selected_plan(self):
        rows = comparison_rows(self.recovery_result)
        self.assertEqual([r['plan_id'] for r in rows], ['P0', 'P1', 'P2', 'P3'])
        self.assertEqual([r['plan_id'] for r in rows if r['selected']],
                         [self.recovery_result.recovery.recommended_plan_id])

    def test_metrics_derive_from_actual_reruns(self):
        rows = comparison_rows(self.recovery_result)
        by_id = {r['plan_id']: r for r in rows}
        actual = {'P0': self.recovery_result.baseline.metrics}
        actual.update({p.plan_id: p.metrics for p in self.recovery_result.tested_plans})
        for plan_id, metrics in actual.items():
            with self.subTest(plan=plan_id):
                row = by_id[plan_id]
                self.assertEqual(row['estimated_reach'], metrics.estimated_reach_count)
                self.assertEqual(row['effective_coverage'], metrics.effective_coverage_count)
                self.assertEqual(row['unresolved_critical'], metrics.unresolved_critical_count)
                self.assertEqual(row['selected_attempts'], metrics.actual_selected_attempts)
                self.assertEqual(row['effective_delta_vs_p0'],
                                 metrics.effective_coverage_count - actual['P0'].effective_coverage_count)

    def test_tradeoff_is_not_hidden(self):
        rows = {r['plan_id']: r for r in comparison_rows(self.recovery_result)}
        self.assertEqual(rows['P0']['estimated_reach'], 961)
        self.assertEqual(rows['P3']['estimated_reach'], 946)
        self.assertEqual(rows['P3']['effective_coverage'], 366)
        self.assertLess(rows['P3']['estimated_reach'], rows['P0']['estimated_reach'])
        self.assertGreater(rows['P3']['effective_coverage'], rows['P0']['effective_coverage'])
        report = render_markdown(self.recovery_result, self.config)
        self.assertIn('| P0 |', report)
        self.assertIn('| P3 |', report)
        self.assertIn('lowering technical reach', report)
        self.assertIn('not** proof', report)
        self.assertIn('Digital-signage', report)

    def test_missing_or_duplicate_evaluations_are_rejected(self):
        self.assertRaises(ValueError, comparison_rows,
                          replace(self.recovery_result, tested_plans=self.recovery_result.tested_plans[:-1]))
        self.assertRaises(ValueError, comparison_rows,
                          replace(self.recovery_result, tested_plans=self.recovery_result.tested_plans + (self.recovery_result.tested_plans[0],)))

    def test_command_creates_markdown(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / 'nested' / 'audit.md'
            self.assertEqual(main(['--stage', 'T+00:00', '--output', str(output)]), 0)
            self.assertTrue(output.exists())
            self.assertIn('Agent 4 decision: P3', output.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
