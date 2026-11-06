
import unittest
from types import SimpleNamespace

from lastmile_ai.schemas import (
    ChannelID,
    EventStage,
    DeliveryStatus
)

from lastmile_ai.agents.delivery import (
    stable_hash_value,
    is_base_failure,
    calculate_base_delay,
    calculate_network_penalty,
    calculate_delivery_outcome,
    classify_arrival_time
)


class TestAgent1Runtime(unittest.TestCase):

    def setUp(self):
        self.resident = SimpleNamespace(
            resident_id="R0001",
            zone="Zone B",
            sms_failed_ev01=True,
            weak_mobile_coverage=True,
            limited_internet=True,
            emergency_app_installed=True,
            in_siren_area=True,
            in_signage_area=True
        )

    def test_reproducibility(self):
        first = stable_hash_value(
            "R0001", "CH01", "failure"
        )
        second = stable_hash_value(
            "R0001", "CH01", "failure"
        )
        self.assertEqual(first, second)

    def test_hash_range(self):
        value = stable_hash_value(
            "R0001", "CH01", "delay"
        )
        self.assertGreaterEqual(value, 0)
        self.assertLess(value, 1)

    def test_base_failure_reproducibility(self):
        first = is_base_failure(
            "R0001", ChannelID.SMS
        )
        second = is_base_failure(
            "R0001", ChannelID.SMS
        )
        self.assertEqual(first, second)

    def test_base_delay_range(self):
        delay = calculate_base_delay(
            "R0001", ChannelID.SMS
        )
        self.assertGreaterEqual(delay, 8)
        self.assertLessEqual(delay, 25)

    def test_network_penalty(self):
        self.assertEqual(
            calculate_network_penalty(
                self.resident, ChannelID.SMS
            ),
            15
        )

        self.assertEqual(
            calculate_network_penalty(
                self.resident, ChannelID.MOBILE_APP
            ),
            20
        )

    def test_ev01_sms_failure(self):
        outcome = calculate_delivery_outcome(
            self.resident,
            ChannelID.SMS,
            EventStage.T02
        )

        self.assertEqual(
            outcome["status"],
            DeliveryStatus.FAILED
        )

        self.assertTrue(outcome["attempted"])

        self.assertIsNone(
            outcome["arrival_time_seconds"]
        )

    def test_delivery_boundaries(self):
        self.assertEqual(
            classify_arrival_time(30),
            DeliveryStatus.DELIVERED
        )

        self.assertEqual(
            classify_arrival_time(31),
            DeliveryStatus.DELAYED
        )

        self.assertEqual(
            classify_arrival_time(60),
            DeliveryStatus.DELAYED
        )

        self.assertEqual(
            classify_arrival_time(61),
            DeliveryStatus.FAILED
        )

    def test_stage_without_network_change(self):
        before = calculate_delivery_outcome(
            self.resident,
            ChannelID.VOICE_CALL,
            EventStage.T00
        )

        after = calculate_delivery_outcome(
            self.resident,
            ChannelID.VOICE_CALL,
            EventStage.T06
        )

        self.assertEqual(before, after)


    def test_same_delivery_across_plans(self):
        from lastmile_ai.agents.delivery import create_selected_delivery_record

        p0 = create_selected_delivery_record(
            self.resident,
            ChannelID.VOICE_CALL,
            EventStage.T04,
            "P0"
        )

        p1 = create_selected_delivery_record(
            self.resident,
            ChannelID.VOICE_CALL,
            EventStage.T04,
            "P1"
        )

        self.assertEqual(p0.status, p1.status)
        self.assertEqual(
            p0.arrival_time_seconds,
            p1.arrival_time_seconds
        )
        self.assertEqual(p0.attempted, p1.attempted)
        self.assertEqual(p0.evidence, p1.evidence)




    def test_selected_vs_potential(self):
        from lastmile_ai.agents.delivery import (
            create_selected_delivery_record,
            create_potential_delivery_record
        )
        from lastmile_ai.schemas import Agent1Output

        selected = create_selected_delivery_record(
            self.resident,
            ChannelID.VOICE_CALL,
            EventStage.T00,
            "P0"
        )

        potential = create_potential_delivery_record(
            self.resident,
            ChannelID.SMS,
            EventStage.T00,
            "P0"
        )

        output = Agent1Output(
            plan_id="P0",
            selected_delivery_records=(selected,),
            potential_channel_evaluations=(potential,),
            no_eligible_assignments=()
        )

        self.assertTrue(selected.selected_in_plan)
        self.assertTrue(selected.attempted)

        self.assertFalse(potential.selected_in_plan)
        self.assertFalse(potential.attempted)
        self.assertIsNone(potential.attempt_time_seconds)

        self.assertEqual(output.actual_attempt_count, 1)

        expected_arrivals = int(
            selected.status in (
                DeliveryStatus.DELIVERED,
                DeliveryStatus.DELAYED
            )
        )

        self.assertEqual(
            output.unique_technical_arrivals,
            expected_arrivals
        )


    def test_no_eligible_channel(self):
        from lastmile_ai.schemas import (
            ResidentProfile,
            SimulationConfiguration,
            PlanAssignment,
            Agent1Input,
            AssignmentStatus
        )
        from lastmile_ai.agents.delivery import run_agent1

        resident = ResidentProfile(
            resident_id="R0002",
            zone="Zone A",
            age=30,
            elderly_65_plus=False,
            hearing_impairment=False,
            visual_impairment=False,
            limited_internet=False,
            weak_mobile_coverage=False,
            emergency_app_installed=False,
            in_siren_area=False,
            in_signage_area=False,
            sms_failed_ev01=False,
            voice_usable=True,
            signage_readable=True,
            policy_age_60_plus=False
        )

        configuration = SimulationConfiguration(
            selected_stage=EventStage.T00,
            enabled_channels=(
                ChannelID.MOBILE_APP,
                ChannelID.DIGITAL_SIGNAGE
            )
        )

        assignment = PlanAssignment(
            resident_id="R0002",
            plan_id="P0",
            assignment_status=AssignmentStatus.NO_ELIGIBLE_CHANNEL,
            selected_channel=None,
            reason="No eligible enabled channel"
        )

        agent_input = Agent1Input(
            configuration=configuration,
            residents=(resident,),
            assignments=(assignment,),
            plan_id="P0"
        )

        output = run_agent1(agent_input)

        self.assertEqual(
            len(output.selected_delivery_records), 0
        )

        self.assertEqual(
            len(output.potential_channel_evaluations), 2
        )

        self.assertEqual(
            len(output.no_eligible_assignments), 1
        )

        self.assertEqual(output.actual_attempt_count, 0)
        self.assertEqual(output.unique_technical_arrivals, 0)

        for record in output.potential_channel_evaluations:
            self.assertFalse(record.selected_in_plan)
            self.assertFalse(record.attempted)
            self.assertEqual(
                record.status,
                DeliveryStatus.UNAVAILABLE
            )

        output.validate_against_input(agent_input)



    def test_ev01_cumulative_stages(self):
        affected = self.resident

        # The same affected SMS channel before the outage
        before = calculate_delivery_outcome(
            affected,
            ChannelID.SMS,
            EventStage.T00
        )

        self.assertNotEqual(
            before["reason"],
            "EV01 SMS outage"
        )

        # EV01 must persist at all later selectable stages
        for stage in (
            EventStage.T02,
            EventStage.T04,
            EventStage.T06
        ):
            with self.subTest(stage=stage):
                outcome = calculate_delivery_outcome(
                    affected,
                    ChannelID.SMS,
                    stage
                )

                self.assertEqual(
                    outcome["status"],
                    DeliveryStatus.FAILED
                )
                self.assertEqual(
                    outcome["reason"],
                    "EV01 SMS outage"
                )
                self.assertTrue(outcome["attempted"])

        # EV02 and EV03 must not alter technical Voice delivery
        voice_results = [
            calculate_delivery_outcome(
                affected,
                ChannelID.VOICE_CALL,
                stage
            )
            for stage in EventStage
        ]

        self.assertTrue(
            all(result == voice_results[0]
                for result in voice_results)
        )



    def test_base_failure_evidence(self):
        from lastmile_ai.agents.delivery import (
            calculate_delivery_outcome,
            stable_hash_value,
            CHANNEL_TIMING_RULES,
            TIMING_MODEL_VERSION
        )

        # Find a deterministic SMS base failure.
        failed_id = next(
            resident_id
            for number in range(1, 10001)
            if (
                resident_id := f"R{number:04d}"
            )
            and stable_hash_value(
                resident_id, "CH01", "failure"
            ) < CHANNEL_TIMING_RULES[
                ChannelID.SMS
            ]["failure_probability"]
        )

        resident = SimpleNamespace(
            **{
                **vars(self.resident),
                "resident_id": failed_id,
                "sms_failed_ev01": False
            }
        )

        result = calculate_delivery_outcome(
            resident,
            ChannelID.SMS,
            EventStage.T00
        )

        self.assertEqual(
            result["status"],
            DeliveryStatus.FAILED
        )
        self.assertEqual(
            result["reason"],
            "Deterministic base failure"
        )

        evidence = result["evidence"]

        self.assertEqual(
            evidence["model_version"],
            TIMING_MODEL_VERSION
        )
        self.assertEqual(
            evidence["failure_probability"],
            0.05
        )
        self.assertLess(
            evidence["failure_hash_value"],
            evidence["failure_probability"]
        )
        self.assertEqual(
            evidence["failure_rule"],
            "hash < probability"
        )



    def test_all_channel_prerequisites(self):
        from lastmile_ai.agents.delivery import calculate_delivery_outcome

        # All hard prerequisites are missing.
        resident = SimpleNamespace(
            **{
                **vars(self.resident),
                "emergency_app_installed": False,
                "in_siren_area": False,
                "in_signage_area": False,
                "sms_failed_ev01": False
            }
        )

        expected = {
            ChannelID.SMS: True,
            ChannelID.VOICE_CALL: True,
            ChannelID.MOBILE_APP: False,
            ChannelID.PUBLIC_SIRENS: False,
            ChannelID.DIGITAL_SIGNAGE: False
        }

        for channel, eligible in expected.items():
            with self.subTest(channel=channel):
                result = calculate_delivery_outcome(
                    resident,
                    channel,
                    EventStage.T00
                )

                if eligible:
                    self.assertNotEqual(
                        result["status"],
                        DeliveryStatus.UNAVAILABLE
                    )
                    self.assertTrue(result["attempted"])
                else:
                    self.assertEqual(
                        result["status"],
                        DeliveryStatus.UNAVAILABLE
                    )
                    self.assertFalse(result["attempted"])
                    self.assertIsNone(
                        result["arrival_time_seconds"]
                    )



    def test_delivery_timeout_over_60_seconds(self):
        from unittest.mock import patch
        from lastmile_ai.agents import delivery

        # Force a 61-second delay for this test only.
        # This does not change the approved model parameters.
        with patch.object(delivery, "is_base_failure", return_value=False),              patch.object(delivery, "calculate_base_delay", return_value=61),              patch.object(delivery, "calculate_network_penalty", return_value=0):

            result = delivery.calculate_delivery_outcome(
                self.resident,
                ChannelID.VOICE_CALL,
                EventStage.T00
            )

        self.assertEqual(
            result["status"],
            DeliveryStatus.FAILED
        )

        self.assertTrue(result["attempted"])

        self.assertIsNone(
            result["arrival_time_seconds"]
        )

        self.assertEqual(
            result["reason"],
            "Delivery exceeded 60-second window"
        )

        self.assertEqual(
            result["evidence"]["calculated_delay_seconds"],
            61
        )

        self.assertEqual(
            result["evidence"]["network_penalty_seconds"],
            0
        )


if __name__ == "__main__":
    unittest.main()
