
import unittest

from lastmile_ai.metrics import (
    count_estimated_reach,
    count_effective_warning_coverage,
    calculate_recovery_improvement,
    count_unresolved_critical_cases,
)

from lastmile_ai.schemas import (
    Agent1Output,
    Agent3Output,
    ChannelID,
    DeliveryRecord,
    DeliveryStatus,
    AccessibilityFinding,
    AccessibilityStatus,
    EvidenceReference,
    EvidenceKind,
    PlanMetrics,
    Agent2Output,
    ResidentRiskFinding,
    RiskPriority,
)


def make_record(resident_id, status, arrival, channel=ChannelID.SMS):
    return DeliveryRecord(
        resident_id=resident_id,
        plan_id="P0",
        channel_id=channel,
        status=status,
        selected_in_plan=True,
        attempted=status != DeliveryStatus.UNAVAILABLE,
        attempt_time_seconds=(
            0 if status != DeliveryStatus.UNAVAILABLE else None
        ),
        arrival_time_seconds=arrival,
        reason="Synthetic test",
        evidence="TEST",
    )


class MetricsTests(unittest.TestCase):

    def test_estimated_reach(self):
        output = Agent1Output(
            plan_id="P0",
            selected_delivery_records=(
                make_record("R0001", DeliveryStatus.DELIVERED, 20),
                make_record("R0002", DeliveryStatus.DELAYED, 45),
                make_record("R0003", DeliveryStatus.FAILED, None),
                make_record("R0004", DeliveryStatus.UNAVAILABLE, None),
            ),
            potential_channel_evaluations=(),
            no_eligible_assignments=(),
        )

        self.assertEqual(count_estimated_reach(output), 2)

    def test_effective_warning_coverage(self):
        deliveries = Agent1Output(
            plan_id="P0",
            selected_delivery_records=(
                make_record("R0001", DeliveryStatus.DELIVERED, 20),
                make_record("R0002", DeliveryStatus.DELAYED, 45),
                make_record("R0003", DeliveryStatus.DELIVERED, 18),
            ),
            potential_channel_evaluations=(),
            no_eligible_assignments=(),
        )

        evidence = (
            EvidenceReference(
                "TEST",
                "Synthetic assessment",
                EvidenceKind.SIMULATION_RECORD,
            ),
        )

        assessment = Agent3Output(
            plan_id="P0",
            accessibility_findings=(
                AccessibilityFinding(
                    "R0001",
                    ChannelID.SMS,
                    AccessibilityStatus.USABLE,
                    "Usable",
                    True,
                    evidence,
                ),
                AccessibilityFinding(
                    "R0002",
                    ChannelID.SMS,
                    AccessibilityStatus.USABLE,
                    "Arrived late",
                    True,
                    evidence,
                ),
                AccessibilityFinding(
                    "R0003",
                    ChannelID.SMS,
                    AccessibilityStatus.BARRIER,
                    "Accessibility barrier",
                    True,
                    evidence,
                ),
            ),
            policy_findings=(),
            cap_advisory=None,
        )

        self.assertEqual(
            count_effective_warning_coverage(deliveries, assessment),
            1,
        )

    def test_public_siren_is_alert_only(self):
        deliveries = Agent1Output(
            plan_id="P0",
            selected_delivery_records=(
                make_record(
                    "R0005",
                    DeliveryStatus.DELIVERED,
                    10,
                    channel=ChannelID.PUBLIC_SIRENS,
                ),
            ),
            potential_channel_evaluations=(),
            no_eligible_assignments=(),
        )

        evidence = (
            EvidenceReference(
                "TEST-SIREN",
                "Synthetic siren assessment",
                EvidenceKind.SIMULATION_RECORD,
            ),
        )

        assessment = Agent3Output(
            plan_id="P0",
            accessibility_findings=(
                AccessibilityFinding(
                    "R0005",
                    ChannelID.PUBLIC_SIRENS,
                    AccessibilityStatus.USABLE,
                    "Audible alert, but no protective instructions",
                    False,
                    evidence,
                ),
            ),
            policy_findings=(),
            cap_advisory=None,
        )

        self.assertEqual(count_estimated_reach(deliveries), 1)
        self.assertEqual(
            count_effective_warning_coverage(deliveries, assessment),
            0,
        )

    def test_recovery_improvement(self):
        baseline = PlanMetrics(
            plan_id="P0",
            estimated_reach_count=700,
            effective_coverage_count=600,
            unresolved_critical_count=100,
            actual_selected_attempts=800,
            resolved_accessibility_gaps=0,
        )

        recovery = PlanMetrics(
            plan_id="P1",
            estimated_reach_count=820,
            effective_coverage_count=740,
            unresolved_critical_count=60,
            actual_selected_attempts=900,
            resolved_accessibility_gaps=40,
        )

        # Improvement: (740 - 600) / 1000 * 100 = 14 points
        self.assertAlmostEqual(
            calculate_recovery_improvement(baseline, recovery),
            14.0,
        )

        unchanged = PlanMetrics(
            plan_id="P2",
            estimated_reach_count=700,
            effective_coverage_count=600,
            unresolved_critical_count=100,
            actual_selected_attempts=800,
            resolved_accessibility_gaps=0,
        )

        self.assertEqual(
            calculate_recovery_improvement(baseline, unchanged),
            0.0,
        )

        regressed = PlanMetrics(
            plan_id="P3",
            estimated_reach_count=700,
            effective_coverage_count=590,
            unresolved_critical_count=110,
            actual_selected_attempts=800,
            resolved_accessibility_gaps=0,
        )

        with self.assertRaises(ValueError):
            calculate_recovery_improvement(baseline, regressed)


    def test_unresolved_critical_cases(self):
        evidence = (
            EvidenceReference(
                "TEST-RISK",
                "Synthetic risk assessment",
                EvidenceKind.SIMULATION_RECORD,
            ),
        )

        priorities = (
            ("R0001", RiskPriority.HIGH),
            ("R0002", RiskPriority.LOW),
            ("R0003", RiskPriority.MEDIUM),
            ("R0004", RiskPriority.HIGH),
        )

        findings = tuple(
            ResidentRiskFinding(
                resident_id=resident_id,
                priority=priority,
                reason="Synthetic test",
                accessibility_review_needed=False,
                evidence=evidence,
            )
            for resident_id, priority in priorities
        )

        risk_results = Agent2Output(
            plan_id="P0",
            resident_risks=findings,
        )

        self.assertEqual(
            count_unresolved_critical_cases(risk_results),
            2,
        )



if __name__ == "__main__":
    unittest.main()
