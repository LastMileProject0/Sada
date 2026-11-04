"""Stage-by-stage real synthetic regressions and AI/plan isolation checks."""
import unittest
from lastmile_ai.schemas import ChannelID, EventStage, SimulationConfiguration
from lastmile_ai.runtime import run_integrated_baseline
from lastmile_ai.recovery_runtime import run_integrated_recovery
from lastmile_ai.ai.maymona_rag_bridge import explain_from_maymona
from test_salma_final_runtime_wiring import ev02_fixture


class FinalStageIsolationTests(unittest.TestCase):
    def test_all_four_stages_resolver_preserves_delivery(self):
        """Only accessibility review changes; simulated delivery is unchanged."""
        for stage in EventStage:
            config = SimulationConfiguration(stage, tuple(ChannelID))
            original = run_integrated_baseline(config)
            staged = run_integrated_baseline(config, stage_barrier_resolver=ev02_fixture)
            self.assertEqual(staged.delivery, original.delivery)
            self.assertEqual(staged.agent1_input.assignments, original.agent1_input.assignments)
            self.assertLessEqual(staged.metrics.effective_coverage_count, original.metrics.effective_coverage_count)

    def test_sms_disabled_with_stage_resolver_is_a_valid_scenario(self):
        """Do not manufacture SMS eligibility or delivery under EV02 checks."""
        enabled = tuple(ch for ch in ChannelID if ch != ChannelID.SMS)
        config = SimulationConfiguration(EventStage.T04, enabled)
        run = run_integrated_recovery(config, stage_barrier_resolver=ev02_fixture)
        self.assertTrue(all(
            a.selected_channel != ChannelID.SMS
            for c in run.recovery.candidates for a in c.assignments
        ))
        self.assertTrue(all(
            a.selected_channel != ChannelID.SMS
            for a in run.baseline.agent1_input.assignments
        ))
        self.assertLessEqual(run.recovery.baseline_metrics.effective_coverage_count,
                             run.recovery.final_metrics.effective_coverage_count)

    def test_ai_sidecar_cannot_change_recovery_plan_or_metrics(self):
        """Actually rerun Agent 4 before and after LLM explanation."""
        config = SimulationConfiguration(EventStage.T02, tuple(ChannelID))
        first = run_integrated_recovery(config)
        before = (first.recovery.recommended_plan_id, first.recovery.final_metrics,
                  tuple((c.plan_id,c.assignments,c.tested_metrics) for c in first.recovery.candidates))
        response = explain_from_maymona(
            'هل غياب تعليمات الحماية يعتبر مخالفة لمعيار CAP؟',
            provider=lambda *_: 'The recommended action field is optional. [SRC-01-E01]'
        )
        self.assertEqual(response.status, 'Answered')
        again = run_integrated_recovery(config)
        after = (again.recovery.recommended_plan_id, again.recovery.final_metrics,
                 tuple((c.plan_id,c.assignments,c.tested_metrics) for c in again.recovery.candidates))
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
