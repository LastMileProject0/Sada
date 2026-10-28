"""First genuine Step 3 end-to-end smoke tests (not mocked agents)."""
import unittest

from lastmile_ai.runtime import build_p0_assignments, run_integrated_baseline
from lastmile_ai.schemas import (
    AssignmentStatus, ChannelID, EventStage, ResidentProfile,
    SimulationConfiguration, RESIDENT_COUNT,
)


def sample_resident(**overrides):
    data = dict(
        resident_id='TEST1', zone='Zone B', age=35,
        elderly_65_plus=False, hearing_impairment=True,
        visual_impairment=False, limited_internet=True,
        weak_mobile_coverage=True, emergency_app_installed=False,
        in_siren_area=False, in_signage_area=False,
        sms_failed_ev01=True, voice_usable=False,
        signage_readable=False, policy_age_60_plus=False,
    )
    data.update(overrides)
    return ResidentProfile(**data)


class ActualRuntimeIntegrationTests(unittest.TestCase):
    def test_baseline_ignores_connectivity_risk_for_hard_eligibility(self):
        config = SimulationConfiguration(EventStage.T02, (ChannelID.VOICE_CALL, ChannelID.SMS))
        assignment, = build_p0_assignments(config, (sample_resident(),))
        self.assertEqual(assignment.selected_channel, ChannelID.SMS)
        self.assertEqual(assignment.assignment_status, AssignmentStatus.ASSIGNED)

    def test_fixed_priority_when_sms_disabled(self):
        config = SimulationConfiguration(EventStage.T04, (ChannelID.MOBILE_APP, ChannelID.VOICE_CALL))
        assignment, = build_p0_assignments(config, (sample_resident(),))
        self.assertEqual(assignment.selected_channel, ChannelID.VOICE_CALL)

    def test_no_eligible_channel_is_assignment_not_attempt(self):
        config = SimulationConfiguration(EventStage.T02, (ChannelID.PUBLIC_SIRENS, ChannelID.DIGITAL_SIGNAGE))
        assignment, = build_p0_assignments(config, (sample_resident(),))
        self.assertEqual(assignment.assignment_status, AssignmentStatus.NO_ELIGIBLE_CHANNEL)
        self.assertIsNone(assignment.selected_channel)

    def test_full_real_team_runtime_with_1000_residents(self):
        config = SimulationConfiguration(EventStage.T02, tuple(ChannelID))
        output = run_integrated_baseline(config)
        self.assertEqual(len(output.residents), RESIDENT_COUNT)
        self.assertEqual(len(output.delivery.selected_delivery_records), RESIDENT_COUNT)
        self.assertEqual(len(output.risks.resident_risks), RESIDENT_COUNT)
        self.assertEqual(len(output.accessibility.accessibility_findings), RESIDENT_COUNT)
        self.assertEqual(output.metrics.actual_selected_attempts, RESIDENT_COUNT)
        self.assertEqual(output.metrics.plan_id, 'P0')
        self.assertEqual(output.metrics.estimated_reach_count, 722)
        # No individual SMS rendering/usability evidence has been supplied.
        self.assertEqual(output.metrics.effective_coverage_count, 0)


if __name__ == '__main__':
    unittest.main()
