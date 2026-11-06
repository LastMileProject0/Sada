"""Focused unit tests for the approved LastMile AI Step 2 data contracts.

These tests exercise schema validation and handoffs only. They do NOT simulate
warning delivery, prove accessibility, establish legal compliance, or validate
1,000-resident recovery metrics. Run from the repository root:
    python -m unittest discover -s tests -p "test_*.py" -v
"""

import unittest

from lastmile_ai.schemas import (
    AccessibilityFinding,
    AccessibilityStatus,
    Agent1Input,
    Agent1Output,
    Agent2Input,
    Agent2Output,
    Agent3Input,
    Agent3Output,
    Agent4Input,
    Agent4Output,
    AssignmentStatus,
    CAPAdvisory,
    CHANNEL_PRIORITY_P0,
    ChannelID,
    DeliveryRecord,
    DeliveryStatus,
    EventStage,
    EvidenceKind,
    EvidenceReference,
    PlanAssignment,
    PlanMetrics,
    PolicyCheckStatus,
    PolicyFinding,
    RecoveryCandidate,
    RecoveryOutcome,
    ResidentProfile,
    ResidentRiskFinding,
    RiskPriority,
    SimulationConfiguration,
)


def resident(resident_id="R0001", *, age=40):
    return ResidentProfile(
        resident_id=resident_id, zone="Zone A", age=age,
        elderly_65_plus=age >= 65, hearing_impairment=False,
        visual_impairment=False, limited_internet=False,
        weak_mobile_coverage=False, emergency_app_installed=True,
        in_siren_area=True, in_signage_area=True, sms_failed_ev01=False,
        voice_usable=True, signage_readable=True,
        policy_age_60_plus=age >= 60,
    )


def config(*channels):
    return SimulationConfiguration(EventStage.T00, tuple(channels or (ChannelID.SMS,)))


def assignment(resident_id="R0001", channel=ChannelID.SMS, plan_id="P0"):
    if channel is None:
        return PlanAssignment(resident_id, plan_id,
                              AssignmentStatus.NO_ELIGIBLE_CHANNEL, None,
                              "No enabled channel meets hard prerequisites")
    return PlanAssignment(resident_id, plan_id, AssignmentStatus.ASSIGNED,
                          channel, "Fixed priority")


def delivery(status=DeliveryStatus.DELIVERED, arrival=20, *,
             selected=True, attempted=True, channel=ChannelID.SMS,
             resident_id="R0001", plan_id="P0"):
    return DeliveryRecord(
        resident_id, plan_id, channel, status, selected, attempted,
        0 if attempted else None, arrival, "Synthetic unit-test case", "TEST",
    )


def ev():
    return (EvidenceReference("TEST", "Synthetic test evidence",
                              EvidenceKind.SIMULATION_RECORD),)


def a1_input(*, channel=ChannelID.SMS, choices=(ChannelID.SMS,)):
    return Agent1Input(config(*choices), (resident(),),
                       (assignment(channel=channel),), "P0")


def a1_output(record=None):
    return Agent1Output("P0", (record or delivery(),), (), ())


def metrics(plan_id="P0", *, reach=1, effective=1, attempts=1, gaps=0, critical=0):
    return PlanMetrics(plan_id, reach, effective, critical, attempts, gaps)


class TestSimulationConfiguration(unittest.TestCase):
    def test_valid_roundtrip_and_priority(self):
        source = {"selected_stage": "T+02:00", "enabled_channels": ["CH03", "CH01"]}
        result = SimulationConfiguration.from_dict(source)
        self.assertEqual(result.selected_stage, EventStage.T02)
        self.assertEqual(result.to_dict()["enabled_channels"], ["CH01", "CH03"])
        self.assertEqual(CHANNEL_PRIORITY_P0,
                         (ChannelID.SMS, ChannelID.VOICE_CALL, ChannelID.MOBILE_APP,
                          ChannelID.PUBLIC_SIRENS, ChannelID.DIGITAL_SIGNAGE))

    def test_rejects_missing_or_extra_planner_inputs(self):
        for raw in ({"selected_stage": "T+00:00"},
                    {"selected_stage": "T+00:00", "enabled_channels": ["CH01"], "population": 1000}):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                SimulationConfiguration.from_dict(raw)

    def test_rejects_wrong_stage_and_channel(self):
        for stage, channels in (("T+07:00", ["CH01"]), ("T+00:00", ["CH06"])):
            with self.subTest(stage=stage, channels=channels), self.assertRaises(ValueError):
                SimulationConfiguration.from_dict(
                    {"selected_stage": stage, "enabled_channels": channels})

    def test_rejects_empty_duplicate_or_wrong_channel_type(self):
        with self.assertRaises(ValueError):
            SimulationConfiguration(EventStage.T00, ())
        with self.assertRaises(ValueError):
            config(ChannelID.SMS, ChannelID.SMS)
        with self.assertRaises(ValueError):
            SimulationConfiguration(EventStage.T00, ("CH01",))

    def test_resident_flags_must_match_age(self):
        with self.assertRaises(ValueError):
            ResidentProfile(**{**resident(age=65).__dict__, "elderly_65_plus": False})
        with self.assertRaises(ValueError):
            ResidentProfile(**{**resident(age=60).__dict__, "policy_age_60_plus": False})
        with self.assertRaises(TypeError):
            ResidentProfile(**{**resident().__dict__, "voice_usable": "Yes"})

    def test_no_eligible_is_assignment_not_delivery_status(self):
        value = assignment(channel=None)
        self.assertEqual(value.assignment_status, AssignmentStatus.NO_ELIGIBLE_CHANNEL)
        self.assertIsNone(value.selected_channel)
        self.assertNotIn("No Eligible Channel", {s.value for s in DeliveryStatus})

    def test_input_rejects_disabled_channel_and_missing_assignment(self):
        with self.assertRaises(ValueError):
            a1_input(channel=ChannelID.VOICE_CALL)
        with self.assertRaises(ValueError):
            Agent1Input(config(ChannelID.SMS), (resident(),), (), "P0")


class TestAgent1DeliveryContracts(unittest.TestCase):
    def test_delivery_boundaries(self):
        for sec, status in ((0, DeliveryStatus.DELIVERED),
                            (30, DeliveryStatus.DELIVERED),
                            (31, DeliveryStatus.DELAYED),
                            (60, DeliveryStatus.DELAYED)):
            with self.subTest(seconds=sec):
                self.assertEqual(delivery(status, sec).status, status)
        with self.assertRaises(ValueError):
            delivery(DeliveryStatus.DELIVERED, 31)
        with self.assertRaises(ValueError):
            delivery(DeliveryStatus.DELAYED, 61)

    def test_failed_unavailable_and_potential_semantics(self):
        self.assertIsNone(delivery(DeliveryStatus.FAILED, None).arrival_time_seconds)
        self.assertFalse(delivery(DeliveryStatus.UNAVAILABLE, None,
                                  attempted=False).attempted)
        with self.assertRaises(ValueError):
            delivery(DeliveryStatus.UNAVAILABLE, 20)
        with self.assertRaises(ValueError):
            delivery(DeliveryStatus.FAILED, 10)
        with self.assertRaises(ValueError):
            delivery(DeliveryStatus.DELIVERED, 20, selected=False, attempted=True)

    def test_selected_record_requires_attempt(self):
        with self.assertRaises(ValueError):
            delivery(DeliveryStatus.DELIVERED, 20, attempted=False)

    def test_agent1_output_rejects_duplicate_selected_record(self):
        rec = delivery()
        with self.assertRaises(ValueError):
            Agent1Output("P0", (rec, rec), (), ())

    def test_agent1_handoff_rejects_wrong_selected_channel(self):
        source = a1_input(choices=(ChannelID.SMS, ChannelID.VOICE_CALL))
        bad = Agent1Output("P0", (delivery(channel=ChannelID.VOICE_CALL),), (), ())
        with self.assertRaises(ValueError):
            bad.validate_against_input(source)

    def test_agent1_no_eligible_handoff_must_match(self):
        source = a1_input(channel=None)
        output = Agent1Output("P0", (), (), (assignment(channel=None),))
        output.validate_against_input(source)
        with self.assertRaises(ValueError):
            Agent1Output("P0", (), (), ()).validate_against_input(source)

    def test_potential_arrival_is_not_selected_attempt_or_reach(self):
        rec = delivery(DeliveryStatus.FAILED, None)
        potential = delivery(DeliveryStatus.DELIVERED, 15, selected=False,
                             attempted=False, channel=ChannelID.VOICE_CALL)
        value = Agent1Output("P0", (rec,), (potential,), ())
        self.assertEqual(value.actual_attempt_count, 1)
        self.assertEqual(value.unique_technical_arrivals, 0)
        value.validate_against_input(a1_input(choices=(ChannelID.SMS, ChannelID.VOICE_CALL)))


class TestAgent2RiskContracts(unittest.TestCase):
    def test_high_medium_low_from_selected_arrival_only(self):
        for record, priority in (
            (delivery(DeliveryStatus.FAILED, None), RiskPriority.HIGH),
            (delivery(DeliveryStatus.DELAYED, 40), RiskPriority.MEDIUM),
            (delivery(DeliveryStatus.DELIVERED, 30), RiskPriority.LOW),
        ):
            with self.subTest(priority=priority.value):
                source = a1_input()
                agent2_input = Agent2Input(source.configuration, source, a1_output(record))
                output = Agent2Output("P0", (ResidentRiskFinding(
                    "R0001", priority, "Actual selected result", False, ev()),))
                output.validate_against_input(agent2_input, require_complete=True)
                wrong = RiskPriority.HIGH if priority != RiskPriority.HIGH else RiskPriority.LOW
                with self.assertRaises(ValueError):
                    Agent2Output("P0", (ResidentRiskFinding(
                        "R0001", wrong, "Wrong priority", False, ev()),)).validate_against_input(agent2_input)

    def test_complete_risk_finding_required_when_requested(self):
        source = a1_input()
        value = Agent2Input(source.configuration, source, a1_output())
        with self.assertRaises(ValueError):
            Agent2Output("P0", ()).validate_against_input(value, require_complete=True)

    def test_duplicate_risks_and_missing_evidence_rejected(self):
        finding = ResidentRiskFinding("R0001", RiskPriority.LOW, "Timed arrival", False, ev())
        with self.assertRaises(ValueError):
            Agent2Output("P0", (finding, finding))
        with self.assertRaises(ValueError):
            ResidentRiskFinding("R0001", RiskPriority.HIGH, "No arrival", False, ())


class TestAgent3PolicyAccessibilityContracts(unittest.TestCase):
    def test_siren_is_alert_only_and_review_is_not_actionable(self):
        with self.assertRaises(ValueError):
            AccessibilityFinding("R0001", ChannelID.PUBLIC_SIRENS,
                                 AccessibilityStatus.USABLE, "Siren arrived", True, ev())
        with self.assertRaises(ValueError):
            AccessibilityFinding("R0001", ChannelID.SMS,
                                 AccessibilityStatus.REVIEW, "Unknown receipt", True, ev())
        with self.assertRaises(ValueError):
            AccessibilityFinding("R0001", ChannelID.SMS,
                                 AccessibilityStatus.NOT_ASSESSED, "No arrival", False, ev())

    def test_policy_fields_and_cap_are_advisory(self):
        a = PolicyFinding("Authorization", PolicyCheckStatus.REVIEW_REQUIRED,
                          "Authorization needs review", ev(), "P0")
        p = PolicyFinding("Privacy", PolicyCheckStatus.INSUFFICIENT_INFO,
                          "Unknown safeguards", ev(), "P0")
        result = Agent3Output("P0", (), (a, p), CAPAdvisory("Advisory only", ("SRC-01",)))
        self.assertEqual(result.cap_advisory.source_ids, ("SRC-01",))
        self.assertEqual(len(result.policy_findings), 2)
        with self.assertRaises(ValueError):
            PolicyFinding("CAP compliance", PolicyCheckStatus.NO_ISSUE, "N/A", ev(), "P0")
        with self.assertRaises(ValueError):
            Agent3Output("P0", (), (a, a), None)

    def test_agent3_accessibility_requires_selected_arrival(self):
        a1 = a1_input()
        fail = a1_output(delivery(DeliveryStatus.FAILED, None))
        risks = Agent2Output("P0", ())
        source = Agent3Input(a1.configuration, a1, fail, risks,
                             "ALWADI-FLOOD-EXERCISE-001", "ACTIONABILITY", "REGISTRY")
        invalid = Agent3Output("P0", (AccessibilityFinding(
            "R0001", ChannelID.SMS, AccessibilityStatus.USABLE,
            "No actual delivery", True, ev()),), (), None)
        with self.assertRaises(ValueError):
            invalid.validate_against_input(source)
        accepted = Agent3Output("P0", (AccessibilityFinding(
            "R0001", ChannelID.SMS, AccessibilityStatus.NOT_ASSESSED,
            "No arrival", None, ev()),), (), None)
        accepted.validate_against_input(source)

    def test_agent3_input_needs_fixture_ids(self):
        a1 = a1_input()
        with self.assertRaises(ValueError):
            Agent3Input(a1.configuration, a1, a1_output(), Agent2Output("P0", ()),
                        "", "ACTIONABILITY", "REGISTRY")


class TestAgent4RecoveryContracts(unittest.TestCase):
    def test_metrics_unique_coverage_bounds(self):
        with self.assertRaises(ValueError):
            metrics(reach=2, effective=3)
        with self.assertRaises(ValueError):
            metrics(reach=1001, effective=1)
        with self.assertRaises(ValueError):
            metrics(reach=1, effective=-1)

    def test_candidate_ids_authorization_and_feasibility(self):
        with self.assertRaises(ValueError):
            RecoveryCandidate("P4", (), True, PolicyCheckStatus.NO_ISSUE, "invalid id")
        with self.assertRaises(ValueError):
            RecoveryCandidate("P1", (), True, PolicyCheckStatus.REVIEW_REQUIRED,
                              "Authorization unresolved", metrics("P1"))
        with self.assertRaises(ValueError):
            RecoveryCandidate("P1", (), False, PolicyCheckStatus.NO_ISSUE,
                              "Not feasible", metrics("P1"))

    def test_no_suitable_recovery_keeps_p0(self):
        baseline = metrics()
        result = Agent4Output(RecoveryOutcome.NO_SUITABLE_PLAN, "P0", baseline,
                              (), baseline, "No tested improvement", ())
        self.assertEqual(result.recovery_improvement_percentage_points, 0)
        with self.assertRaises(ValueError):
            Agent4Output(RecoveryOutcome.NO_SUITABLE_PLAN, "P0", baseline,
                         (), metrics("P0", reach=0, effective=0),
                         "Cannot change P0", ())

    def test_selected_recovery_must_be_tested_and_nonregressive(self):
        baseline = metrics(effective=1, reach=1)
        improved = metrics("P1", effective=2, reach=2, attempts=2)
        candidate = RecoveryCandidate("P1", (), True, PolicyCheckStatus.NO_ISSUE,
                                      "Approved synthetic candidate", improved)
        result = Agent4Output(RecoveryOutcome.PLAN_SELECTED, "P1", baseline,
                              (candidate,), improved, "Improved", ())
        self.assertAlmostEqual(result.recovery_improvement_percentage_points, 0.1)
        with self.assertRaises(ValueError):
            Agent4Output(RecoveryOutcome.PLAN_SELECTED, "P2", baseline,
                         (candidate,), metrics("P2"), "Untested plan", ())
        with self.assertRaises(ValueError):
            Agent4Output(RecoveryOutcome.PLAN_SELECTED, "P1", baseline,
                         (RecoveryCandidate("P1", (), True,
                          PolicyCheckStatus.NO_ISSUE, "regression",
                          metrics("P1", reach=0, effective=0)),),
                         metrics("P1", reach=0, effective=0), "Regression", ())

    def test_recovery_cannot_use_disabled_channel(self):
        baseline = metrics()
        a1 = a1_input()
        source = Agent4Input(a1.configuration, baseline, Agent2Output("P0", ()),
                             Agent3Output("P0", (), (), None), (resident(),))
        candidate = RecoveryCandidate("P1", (assignment(channel=ChannelID.VOICE_CALL,
                                                       plan_id="P1"),),
                                      False, PolicyCheckStatus.REVIEW_REQUIRED,
                                      "Not evaluated")
        value = Agent4Output(RecoveryOutcome.NO_SUITABLE_PLAN, "P0", baseline,
                             (candidate,), baseline, "No approved plan", ())
        with self.assertRaises(ValueError):
            value.validate_against_input(source)

    def test_no_more_than_three_candidates(self):
        baseline = metrics()
        candidate = RecoveryCandidate("P1", (), False, PolicyCheckStatus.REVIEW_REQUIRED,
                                      "Not tested")
        with self.assertRaises(ValueError):
            Agent4Output(RecoveryOutcome.NO_SUITABLE_PLAN, "P0", baseline,
                         (candidate, candidate, candidate, candidate), baseline,
                         "Duplicate and too many", ())


if __name__ == "__main__":
    unittest.main()
