import unittest

from lastmile_ai.runtime import run_integrated_baseline
from lastmile_ai.schemas import (
    SimulationConfiguration,
    EventStage,
    ChannelID,
)


class TestStep4ScenarioValidation(unittest.TestCase):

    def test_reproducibility_same_configuration(self):
        """The same scenario must produce identical simulation results."""

        configuration = SimulationConfiguration(
            selected_stage=EventStage.T02,
            enabled_channels=(
                ChannelID.SMS,
                ChannelID.MOBILE_APP,
                ChannelID.VOICE_CALL,
                ChannelID.PUBLIC_SIRENS,
                ChannelID.DIGITAL_SIGNAGE,
            ),
        )

        first_run = run_integrated_baseline(configuration)
        second_run = run_integrated_baseline(configuration)

        self.assertEqual(first_run, second_run)

    def test_zero_enabled_channels_rejected(self):
        """The configuration must reject zero enabled channels."""

        with self.assertRaises(ValueError):
            SimulationConfiguration(
                selected_stage=EventStage.T02,
                enabled_channels=(),
            )

    def test_delivery_timing_boundaries(self):
        """Validate the approved 30s and 60s delivery boundaries."""

        from lastmile_ai.agents.delivery import classify_arrival_time
        from lastmile_ai.schemas import DeliveryStatus

        expected_results = {
            0: DeliveryStatus.DELIVERED,
            30: DeliveryStatus.DELIVERED,
            31: DeliveryStatus.DELAYED,
            60: DeliveryStatus.DELAYED,
            61: DeliveryStatus.FAILED,
        }

        for seconds, expected_status in expected_results.items():
            with self.subTest(seconds=seconds):
                self.assertEqual(
                    classify_arrival_time(seconds),
                    expected_status,
                )

    def test_no_eligible_channel_and_unavailable(self):
        """Validate No Eligible Channel and Unavailable behavior."""

        from lastmile_ai.schemas import (
            ResidentProfile,
            PlanAssignment,
            Agent1Input,
            AssignmentStatus,
            DeliveryStatus,
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
            policy_age_60_plus=False,
        )

        configuration = SimulationConfiguration(
            selected_stage=EventStage.T00,
            enabled_channels=(
                ChannelID.MOBILE_APP,
                ChannelID.DIGITAL_SIGNAGE,
            ),
        )

        assignment = PlanAssignment(
            resident_id="R0002",
            plan_id="P0",
            assignment_status=AssignmentStatus.NO_ELIGIBLE_CHANNEL,
            selected_channel=None,
            reason="No eligible enabled channel",
        )

        agent_input = Agent1Input(
            configuration=configuration,
            residents=(resident,),
            assignments=(assignment,),
            plan_id="P0",
        )

        output = run_agent1(agent_input)

        self.assertEqual(len(output.selected_delivery_records), 0)
        self.assertEqual(len(output.no_eligible_assignments), 1)
        self.assertEqual(len(output.potential_channel_evaluations), 2)

        self.assertEqual(output.actual_attempt_count, 0)
        self.assertEqual(output.unique_technical_arrivals, 0)

        for record in output.potential_channel_evaluations:
            with self.subTest(channel=record.channel_id):
                self.assertEqual(
                    record.status,
                    DeliveryStatus.UNAVAILABLE,
                )
                self.assertFalse(record.attempted)
                self.assertFalse(record.selected_in_plan)
                self.assertIsNone(record.attempt_time_seconds)
                self.assertIsNone(record.arrival_time_seconds)

        output.validate_against_input(agent_input)

    def test_four_stage_scenario_matrix(self):
        """Validate all four stages with all five channels enabled."""

        all_channels = (
            ChannelID.SMS,
            ChannelID.MOBILE_APP,
            ChannelID.VOICE_CALL,
            ChannelID.PUBLIC_SIRENS,
            ChannelID.DIGITAL_SIGNAGE,
        )

        for stage in (
            EventStage.T00,
            EventStage.T02,
            EventStage.T04,
            EventStage.T06,
        ):
            with self.subTest(stage=stage):
                configuration = SimulationConfiguration(
                    selected_stage=stage,
                    enabled_channels=all_channels,
                )

                result = run_integrated_baseline(configuration)

                self.assertIsNotNone(result)
                self.assertEqual(
                    result.delivery.plan_id,
                    "P0",
                )

    def test_each_channel_individually_at_t02(self):
        """Run each approved channel individually at T+02."""

        channels = (
            ChannelID.SMS,
            ChannelID.MOBILE_APP,
            ChannelID.VOICE_CALL,
            ChannelID.PUBLIC_SIRENS,
            ChannelID.DIGITAL_SIGNAGE,
        )

        for channel in channels:
            with self.subTest(channel=channel):
                configuration = SimulationConfiguration(
                    selected_stage=EventStage.T02,
                    enabled_channels=(channel,),
                )

                result = run_integrated_baseline(configuration)

                self.assertEqual(result.delivery.plan_id, "P0")

                selected = result.delivery.selected_delivery_records
                potential = result.delivery.potential_channel_evaluations
                no_eligible = result.delivery.no_eligible_assignments

                # Every resident has a selected assignment
                # or a No Eligible Channel assignment.
                self.assertEqual(
                    len(selected) + len(no_eligible),
                    len(result.residents),
                )

                # Selected records use only the enabled channel.
                self.assertTrue(
                    all(
                        record.channel_id == channel
                        for record in selected
                    )
                )

                # Potential records cannot use disabled channels.
                self.assertTrue(
                    all(
                        record.channel_id == channel
                        for record in potential
                    )
                )

    def test_cumulative_event_activation(self):
        """Validate cumulative EV01, EV02 and EV03 activation."""

        from lastmile_ai.agents.scenario_conditions import (
            is_sms_outage_active,
            is_ev02_active,
            is_ev03_active,
        )
        from types import SimpleNamespace

        affected_resident = SimpleNamespace(
            zone="Zone B",
            sms_failed_ev01=True,
        )

        expected = {
            EventStage.T00: (False, False, False),
            EventStage.T02: (True, False, False),
            EventStage.T04: (True, True, False),
            EventStage.T06: (True, True, True),
        }

        for stage, expected_flags in expected.items():
            with self.subTest(stage=stage):
                actual_flags = (
                    is_sms_outage_active(affected_resident, stage),
                    is_ev02_active(stage),
                    is_ev03_active(stage),
                )

                self.assertEqual(actual_flags, expected_flags)

    def test_ev01_zone_b_sms_outage(self):
        """Validate the approved 245 EV01 SMS failures in Zone B."""

        from lastmile_ai.schemas import DeliveryStatus

        configuration = SimulationConfiguration(
            selected_stage=EventStage.T02,
            enabled_channels=tuple(ChannelID),
        )

        result = run_integrated_baseline(configuration)

        residents_by_id = {
            resident.resident_id: resident
            for resident in result.residents
        }

        affected = [
            record
            for record in result.delivery.selected_delivery_records
            if record.reason == "EV01 SMS outage"
        ]

        self.assertEqual(len(affected), 245)

        for record in affected:
            with self.subTest(resident_id=record.resident_id):
                resident = residents_by_id[record.resident_id]

                self.assertEqual(resident.zone, "Zone B")
                self.assertTrue(resident.sms_failed_ev01)
                self.assertEqual(record.channel_id, ChannelID.SMS)
                self.assertEqual(record.status, DeliveryStatus.FAILED)
                self.assertTrue(record.attempted)
                self.assertIsNone(record.arrival_time_seconds)

    def test_ev02_accessibility_barriers_at_t04(self):
        """Validate approved Zone B accessibility scenario flags."""

        configuration = SimulationConfiguration(
            selected_stage=EventStage.T04,
            enabled_channels=tuple(ChannelID),
        )

        result = run_integrated_baseline(configuration)

        hearing_barriers = [
            resident
            for resident in result.residents
            if resident.zone == "Zone B"
            and resident.hearing_impairment
            and not resident.voice_usable
        ]

        visual_barriers = [
            resident
            for resident in result.residents
            if resident.zone == "Zone B"
            and resident.visual_impairment
            and not resident.signage_readable
        ]

        self.assertEqual(len(hearing_barriers), 30)
        self.assertEqual(len(visual_barriers), 20)


    def test_four_stage_delivery_results(self):
        """Verify recorded P0 delivery results across all four stages."""

        from collections import Counter
        from lastmile_ai.schemas import DeliveryStatus

        expected = {
            EventStage.T00: (904, 57, 39, 0, 0),
            EventStage.T02: (677, 45, 278, 0, 0),
            EventStage.T04: (677, 45, 278, 0, 0),
            EventStage.T06: (677, 45, 278, 0, 0),
        }

        for stage, expected_counts in expected.items():
            with self.subTest(stage=stage):
                configuration = SimulationConfiguration(
                    selected_stage=stage,
                    enabled_channels=tuple(ChannelID),
                )
                result = run_integrated_baseline(configuration)
                counts = Counter(
                    record.status
                    for record in result.delivery.selected_delivery_records
                )
                actual = (
                    counts[DeliveryStatus.DELIVERED],
                    counts[DeliveryStatus.DELAYED],
                    counts[DeliveryStatus.FAILED],
                    counts[DeliveryStatus.UNAVAILABLE],
                    len(result.delivery.no_eligible_assignments),
                )
                self.assertEqual(actual, expected_counts)
                self.assertEqual(
                    len(result.delivery.selected_delivery_records)
                    + len(result.delivery.no_eligible_assignments),
                    len(result.residents),
                )
                self.assertEqual(len(result.residents), 1000)


if __name__ == "__main__":
    unittest.main()