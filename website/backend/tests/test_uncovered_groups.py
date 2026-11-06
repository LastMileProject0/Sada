
import unittest

from lastmile_ai.metrics import count_uncovered_groups
from lastmile_ai.schemas import (
    ResidentProfile,
    Agent1Output,
    Agent3Output,
    DeliveryRecord,
    DeliveryStatus,
    ChannelID,
    AccessibilityFinding,
    AccessibilityStatus,
    EvidenceReference,
    EvidenceKind,
)


def make_resident(
    resident_id, age,
    hearing=False, visual=False,
    limited=False, weak=False,
):
    return ResidentProfile(
        resident_id=resident_id,
        zone="Zone A",
        age=age,
        elderly_65_plus=age >= 65,
        hearing_impairment=hearing,
        visual_impairment=visual,
        limited_internet=limited,
        weak_mobile_coverage=weak,
        emergency_app_installed=False,
        in_siren_area=False,
        in_signage_area=False,
        sms_failed_ev01=False,
        voice_usable=True,
        signage_readable=True,
        policy_age_60_plus=age >= 60,
    )


def make_delivery(resident_id, status, seconds):
    return DeliveryRecord(
        resident_id=resident_id,
        plan_id="P0",
        channel_id=ChannelID.SMS,
        status=status,
        selected_in_plan=True,
        attempted=True,
        attempt_time_seconds=0,
        arrival_time_seconds=seconds,
        reason="Synthetic test",
        evidence="TEST",
    )


class UncoveredGroupsTests(unittest.TestCase):

    def test_overlapping_groups_count_unique_residents(self):
        residents = (
            make_resident(
                "R0001", 70,
                hearing=True, visual=True,
                limited=True, weak=True,
            ),
            make_resident(
                "R0002", 40,
                visual=True, weak=True,
            ),
            make_resident(
                "R0003", 32,
                hearing=True, limited=True,
                weak=True,
            ),
        )

        deliveries = Agent1Output(
            plan_id="P0",
            selected_delivery_records=(
                make_delivery(
                    "R0001", DeliveryStatus.DELAYED, 45
                ),
                make_delivery(
                    "R0002", DeliveryStatus.DELIVERED, 18
                ),
                make_delivery(
                    "R0003", DeliveryStatus.DELIVERED, 20
                ),
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

        assessments = Agent3Output(
            plan_id="P0",
            accessibility_findings=(
                AccessibilityFinding(
                    "R0001",
                    ChannelID.SMS,
                    AccessibilityStatus.USABLE,
                    "Late arrival",
                    True,
                    evidence,
                ),
                AccessibilityFinding(
                    "R0002",
                    ChannelID.SMS,
                    AccessibilityStatus.BARRIER,
                    "Not usable",
                    True,
                    evidence,
                ),
                AccessibilityFinding(
                    "R0003",
                    ChannelID.SMS,
                    AccessibilityStatus.USABLE,
                    "Usable",
                    True,
                    evidence,
                ),
            ),
            policy_findings=(),
            cap_advisory=None,
        )

        result = count_uncovered_groups(
            residents,
            deliveries,
            assessments,
        )

        self.assertEqual(
            result,
            {
                "hearing_impairment": 1,
                "visual_impairment": 2,
                "elderly_65_plus": 1,
                "limited_internet": 1,
                "weak_mobile_coverage": 2,
                "unique_uncovered_total": 2,
            },
        )


if __name__ == "__main__":
    unittest.main()
