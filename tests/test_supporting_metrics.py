
import unittest

from lastmile_ai.metrics import (
    summarize_policy_assessment,
    summarize_decision_traceability,
)

from lastmile_ai.schemas import (
    Agent1Output,
    Agent2Output,
    Agent3Output,
    AccessibilityFinding,
    AccessibilityStatus,
    ChannelID,
    DeliveryRecord,
    DeliveryStatus,
    EvidenceReference,
    EvidenceKind,
    PolicyFinding,
    PolicyCheckStatus,
    ResidentRiskFinding,
    RiskPriority,
)


def evidence():
    return (
        EvidenceReference(
            "TEST",
            "Synthetic test only",
            EvidenceKind.SIMULATION_RECORD,
        ),
    )


class SupportingMetricsTests(unittest.TestCase):

    def test_policy_keeps_checks_separate(self):
        assessment = Agent3Output(
            "P0",
            (),
            (
                PolicyFinding(
                    "Authorization",
                    PolicyCheckStatus.NO_ISSUE,
                    "Synthetic scenario",
                    evidence(),
                    "P0",
                ),
                PolicyFinding(
                    "Privacy",
                    PolicyCheckStatus.REVIEW_REQUIRED,
                    "Review pending",
                    evidence(),
                    "P0",
                ),
            ),
            None,
        )

        result = summarize_policy_assessment(assessment)

        self.assertEqual(result, {
            "Authorization": "No Issue Identified",
            "Privacy": "Review Required",
        })

    def test_missing_policy_is_not_approved(self):
        assessment = Agent3Output("P0", (), (), None)

        self.assertEqual(
            summarize_policy_assessment(assessment),
            {
                "Authorization": "Not Reported",
                "Privacy": "Not Reported",
            },
        )

    def test_traceability_detects_missing_evidence(self):
        delivery = Agent1Output(
            "P0",
            (
                DeliveryRecord(
                    "R0001", "P0", ChannelID.SMS,
                    DeliveryStatus.DELIVERED,
                    True, True, 0, 15,
                    "Test", "EVENT-1",
                ),
            ),
            (),
            (),
        )

        risks = Agent2Output(
            "P0",
            (
                ResidentRiskFinding(
                    "R0001",
                    RiskPriority.LOW,
                    "On time",
                    False,
                    evidence(),
                ),
            ),
        )

        assessment = Agent3Output(
            "P0",
            (
                AccessibilityFinding(
                    "R0001",
                    ChannelID.SMS,
                    AccessibilityStatus.USABLE,
                    "Test",
                    True,
                    (),
                ),
            ),
            (),
            None,
        )

        result = summarize_decision_traceability(
            delivery, risks, assessment
        )

        self.assertEqual(result, {
            "findings_total": 3,
            "findings_with_evidence": 2,
            "findings_missing_evidence": 1,
            "cap_advisory_source_count": 0,
        })

    def test_traceability_rejects_plan_mismatch(self):
        delivery = Agent1Output("P0", (), (), ())
        risks = Agent2Output("P1", ())
        assessment = Agent3Output("P0", (), (), None)

        with self.assertRaises(ValueError):
            summarize_decision_traceability(
                delivery, risks, assessment
            )


if __name__ == "__main__":
    unittest.main()
