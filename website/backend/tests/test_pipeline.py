"""Unit checks for Sereen's pipeline; test adapters are NOT real agents."""
import unittest

from lastmile_ai.pipeline import AgentRunners, run_baseline, make_recovery_input
from lastmile_ai.schemas import (
    Agent1Output, Agent2Output, Agent3Output, AssignmentStatus,
    AccessibilityFinding, AccessibilityStatus, ChannelID,
    DeliveryRecord, DeliveryStatus, EventStage, EvidenceKind,
    EvidenceReference, PlanAssignment, ResidentProfile,
    ResidentRiskFinding, RiskPriority, SimulationConfiguration,
    RESIDENT_COUNT,
)


def residents_and_assignments():
    residents = tuple(
        ResidentProfile(
            resident_id=f'R{i:04d}', zone='Zone A', age=30,
            elderly_65_plus=False, hearing_impairment=False,
            visual_impairment=False, limited_internet=False,
            weak_mobile_coverage=False, emergency_app_installed=True,
            in_siren_area=True, in_signage_area=True,
            sms_failed_ev01=False, voice_usable=True,
            signage_readable=True, policy_age_60_plus=False,
        )
        for i in range(1, RESIDENT_COUNT + 1)
    )
    assignments = tuple(
        PlanAssignment(r.resident_id, 'P0', AssignmentStatus.ASSIGNED,
                       ChannelID.SMS, 'Synthetic test assignment')
        for r in residents
    )
    return residents, assignments


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.residents, self.assignments = residents_and_assignments()
        self.config = SimulationConfiguration(EventStage.T00, (ChannelID.SMS,))
        self.evidence = (EvidenceReference('TEST', 'Unit test', EvidenceKind.SIMULATION_RECORD),)

    def runners(self, *, wrong_risks=False, missing_delivery=False):
        def agent1(value):
            selected = tuple(
                DeliveryRecord(
                    a.resident_id, 'P0', ChannelID.SMS,
                    DeliveryStatus.DELIVERED, True, True, 0, 10,
                    'Synthetic test', 'TEST',
                )
                for a in value.assignments if a.assignment_status == AssignmentStatus.ASSIGNED
            )
            if missing_delivery:
                selected = selected[:-1]
            return Agent1Output('P0', selected, (), ())

        def agent2(value):
            priority = RiskPriority.HIGH if wrong_risks else RiskPriority.LOW
            return Agent2Output('P0', tuple(
                ResidentRiskFinding(
                    r.resident_id, priority, 'Synthetic test', False, self.evidence,
                )
                for r in value.agent1_input.residents
            ))

        def agent3(value):
            return Agent3Output('P0', tuple(
                AccessibilityFinding(
                    r.resident_id, ChannelID.SMS,
                    AccessibilityStatus.USABLE, 'Synthetic test', True, self.evidence,
                )
                for r in value.agent1_input.residents
            ), (), None)

        return AgentRunners(agent1, agent2, agent3)

    def baseline(self, runners):
        return run_baseline(
            self.config, self.residents, self.assignments, runners,
            warning_fixture_id='ALWADI-FLOOD-EXERCISE-001',
            actionability_rules_id='channel_actionability.md',
            source_registry_id='sources_registry.json',
        )

    def test_baseline_handoff_and_metrics(self):
        result = self.baseline(self.runners())
        self.assertEqual(result.metrics.estimated_reach_count, RESIDENT_COUNT)
        self.assertEqual(result.metrics.effective_coverage_count, RESIDENT_COUNT)
        self.assertEqual(result.metrics.unresolved_critical_count, 0)
        self.assertEqual(result.metrics.actual_selected_attempts, RESIDENT_COUNT)
        self.assertEqual(result.metrics.resolved_accessibility_gaps, 0)
        handoff = make_recovery_input(result)
        self.assertEqual(handoff.baseline_metrics, result.metrics)
        self.assertEqual(handoff.residents, self.residents)

    def test_rejects_missing_selected_delivery(self):
        with self.assertRaisesRegex(ValueError, 'exactly one selected'):
            self.baseline(self.runners(missing_delivery=True))

    def test_rejects_risk_inconsistent_with_arrival(self):
        with self.assertRaisesRegex(ValueError, 'Risk priority conflicts'):
            self.baseline(self.runners(wrong_risks=True))

    def test_requires_fixed_population(self):
        with self.assertRaisesRegex(ValueError, 'fixed 1000-resident'):
            run_baseline(
                self.config, self.residents[:2], self.assignments[:2], self.runners(),
                warning_fixture_id='fixture', actionability_rules_id='rules',
                source_registry_id='sources',
            )


if __name__ == '__main__':
    unittest.main()
