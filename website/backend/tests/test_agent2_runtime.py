"""Tests for LastMile AI Agent 2 runtime. Run: python -m unittest -v test_agent2_runtime.py"""
import unittest

from lastmile_ai.agents.risk import analyze_risk
from lastmile_ai.schemas import (
    Agent1Input, Agent1Output, Agent2Input, AssignmentStatus, ChannelID,
    DeliveryRecord, DeliveryStatus, EventStage, PlanAssignment,
    ResidentProfile, RiskPriority, SimulationConfiguration,
)


def profile(resident_id, *, voice_usable=True, signage_readable=True,
            hearing_impairment=False, visual_impairment=False):
    return ResidentProfile(
        resident_id=resident_id, zone="Zone A", age=30,
        elderly_65_plus=False, hearing_impairment=hearing_impairment,
        visual_impairment=visual_impairment, limited_internet=False,
        weak_mobile_coverage=False, emergency_app_installed=True,
        in_siren_area=True, in_signage_area=True, sms_failed_ev01=False,
        voice_usable=voice_usable, signage_readable=signage_readable,
        policy_age_60_plus=False,
    )


def record(rid, channel, status, elapsed=None, *, selected=True):
    attempted = selected and status != DeliveryStatus.UNAVAILABLE
    return DeliveryRecord(
        resident_id=rid, plan_id="P0", channel_id=channel,
        status=status, selected_in_plan=selected, attempted=attempted,
        attempt_time_seconds=0 if attempted else None,
        arrival_time_seconds=elapsed,
        reason="Test scenario delivery", evidence="Test fixture",
    )


def make_input(profiles, assignments, selected=(), potential=()):
    config = SimulationConfiguration(EventStage.T02, tuple(ChannelID))
    agent1_input = Agent1Input(config, tuple(profiles), tuple(assignments), "P0")
    agent1_output = Agent1Output(
        "P0", tuple(selected), tuple(potential),
        tuple(a for a in assignments if a.assignment_status == AssignmentStatus.NO_ELIGIBLE_CHANNEL),
    )
    return Agent2Input(config, agent1_input, agent1_output)


def assigned(rid, channel=None):
    status = AssignmentStatus.ASSIGNED if channel is not None else AssignmentStatus.NO_ELIGIBLE_CHANNEL
    return PlanAssignment(rid, "P0", status, channel, "Test assignment")


class TestAgent2Runtime(unittest.TestCase):
    def test_arrival_boundaries_and_failure(self):
        people = [profile(f"R{i}") for i in range(1, 6)]
        assignments = [assigned(f"R{i}", ChannelID.SMS) for i in range(1, 5)]
        assignments.append(assigned("R5"))
        selected = [
            record("R1", ChannelID.SMS, DeliveryStatus.DELIVERED, 30),
            record("R2", ChannelID.SMS, DeliveryStatus.DELAYED, 31),
            record("R3", ChannelID.SMS, DeliveryStatus.DELAYED, 60),
            record("R4", ChannelID.SMS, DeliveryStatus.FAILED),
        ]
        result = analyze_risk(make_input(people, assignments, selected))
        priorities = {x.resident_id: x.priority for x in result.resident_risks}
        self.assertEqual(priorities, {
            "R1": RiskPriority.LOW, "R2": RiskPriority.MEDIUM,
            "R3": RiskPriority.MEDIUM, "R4": RiskPriority.HIGH,
            "R5": RiskPriority.HIGH,
        })
        self.assertTrue(all(f.evidence for f in result.resident_risks))

    def test_potential_arrival_must_not_lower_risk(self):
        value = make_input(
            [profile("R1")], [assigned("R1", ChannelID.SMS)],
            [record("R1", ChannelID.SMS, DeliveryStatus.FAILED)],
            [record("R1", ChannelID.MOBILE_APP, DeliveryStatus.DELIVERED, 10, selected=False)],
        )
        self.assertEqual(analyze_risk(value).resident_risks[0].priority, RiskPriority.HIGH)

    def test_disability_alone_is_not_technical_risk(self):
        value = make_input(
            [profile("R1", hearing_impairment=True)],
            [assigned("R1", ChannelID.SMS)],
            [record("R1", ChannelID.SMS, DeliveryStatus.DELIVERED, 5)],
        )
        finding = analyze_risk(value).resident_risks[0]
        self.assertEqual(finding.priority, RiskPriority.LOW)
        self.assertFalse(finding.accessibility_review_needed)

    def test_selected_voice_barrier_is_flagged_separately(self):
        value = make_input(
            [profile("R1", voice_usable=False, hearing_impairment=True)],
            [assigned("R1", ChannelID.VOICE_CALL)],
            [record("R1", ChannelID.VOICE_CALL, DeliveryStatus.DELIVERED, 12)],
        )
        finding = analyze_risk(value).resident_risks[0]
        self.assertEqual(finding.priority, RiskPriority.LOW)
        self.assertTrue(finding.accessibility_review_needed)
        self.assertEqual(len(finding.evidence), 2)

    def test_selected_signage_barrier_is_flagged(self):
        value = make_input(
            [profile("R1", signage_readable=False, visual_impairment=True)],
            [assigned("R1", ChannelID.DIGITAL_SIGNAGE)],
            [record("R1", ChannelID.DIGITAL_SIGNAGE, DeliveryStatus.DELAYED, 50)],
        )
        finding = analyze_risk(value).resident_risks[0]
        self.assertEqual(finding.priority, RiskPriority.MEDIUM)
        self.assertTrue(finding.accessibility_review_needed)

    def test_unavailable_is_high(self):
        value = make_input(
            [profile("R1")], [assigned("R1", ChannelID.MOBILE_APP)],
            [record("R1", ChannelID.MOBILE_APP, DeliveryStatus.UNAVAILABLE)],
        )
        self.assertEqual(analyze_risk(value).resident_risks[0].priority, RiskPriority.HIGH)

    def test_reject_multiple_selected_channels_under_current_contract(self):
        # Current Step 2 schema requires the selected record to match the
        # single assigned channel. Escalate any multi-attempt design to Sirin.
        with self.assertRaises(ValueError):
            make_input(
                [profile("R1")], [assigned("R1", ChannelID.SMS)],
                [record("R1", ChannelID.SMS, DeliveryStatus.DELAYED, 40),
                 record("R1", ChannelID.VOICE_CALL, DeliveryStatus.DELIVERED, 20)],
            )

    def test_reject_non_agent2_input(self):
        with self.assertRaises(TypeError):
            analyze_risk({})


if __name__ == "__main__":
    unittest.main()
