"""Unmocked end-to-end Agent 4 tests with the approved 1,000-resident dataset."""
import unittest

from lastmile_ai.recovery_runtime import effective_resident_ids, run_integrated_recovery
from lastmile_ai.schemas import ChannelID, EventStage, PolicyCheckStatus, RecoveryOutcome, SimulationConfiguration


class RecoveryIntegrationTests(unittest.TestCase):
    def test_three_real_candidate_reruns_and_p3_selection(self):
        result = run_integrated_recovery(SimulationConfiguration(EventStage.T02, tuple(ChannelID)))
        self.assertEqual([r.plan_id for r in result.tested_plans], ['P1', 'P2', 'P3'])
        self.assertEqual(result.baseline.metrics.estimated_reach_count, 722)
        self.assertEqual(result.recovery.recommended_plan_id, 'P3')
        self.assertEqual(result.recovery.outcome, RecoveryOutcome.PLAN_SELECTED)
        self.assertEqual(result.recovery.final_metrics.effective_coverage_count, 366)
        self.assertEqual(result.recovery.final_metrics.estimated_reach_count, 942)
        for plan in result.tested_plans:
            self.assertEqual(len(plan.risks.resident_risks), 1000)
            self.assertEqual(len(plan.accessibility.accessibility_findings), 1000)
            self.assertEqual(plan.metrics.effective_coverage_count,
                             len(effective_resident_ids(plan.delivery, plan.accessibility)))
            self.assertTrue(plan.modeled_prerequisites_pass)

    def test_ev03_external_review_not_conflated_with_internal_channels(self):
        result = run_integrated_recovery(SimulationConfiguration(EventStage.T06, tuple(ChannelID)))
        self.assertEqual(result.recovery.recommended_plan_id, 'P3')
        self.assertTrue(all(c.authorization_status == PolicyCheckStatus.NO_ISSUE
                            for c in result.recovery.candidates))
        # Underlying policy review remains documented, not silently erased.
        self.assertTrue(all(any(p.status == PolicyCheckStatus.REVIEW_REQUIRED
                                for p in plan.accessibility.policy_findings)
                            for plan in result.tested_plans))

    def test_sirens_alone_do_not_count_as_effective_warning(self):
        result = run_integrated_recovery(SimulationConfiguration(EventStage.T02, (ChannelID.PUBLIC_SIRENS,)))
        self.assertEqual(result.baseline.metrics.effective_coverage_count, 0)
        self.assertEqual(result.recovery.recommended_plan_id, 'P0')
        self.assertTrue(all(p.metrics.effective_coverage_count == 0 for p in result.tested_plans))

    def test_enabled_channels_never_expand(self):
        enabled = (ChannelID.SMS, ChannelID.VOICE_CALL)
        result = run_integrated_recovery(SimulationConfiguration(EventStage.T02, enabled))
        self.assertTrue(all(a.selected_channel in enabled or a.selected_channel is None
                            for c in result.recovery.candidates for a in c.assignments))


if __name__ == '__main__':
    unittest.main()
