"""Ethar's isolated EV02 stage-aware accessibility handoff tests.

Run from the repository root:
python -m unittest discover -s tests -p "test_accessibility_stage_ethar.py" -v
No Agents or Master Dataset modifications are performed.
"""
import unittest
from collections import Counter
from dataclasses import replace

from lastmile_ai.accessibility_stage import BarrierStatus, assess_accessibility_barrier
from lastmile_ai.data.resident_adapter import load_resident_profiles
from lastmile_ai.schemas import ChannelID, EventStage, SimulationConfiguration


class EtharStageAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.residents = load_resident_profiles()
        cls.by_id = {resident.resident_id: resident for resident in cls.residents}
        cls.voice_cases = [
            r for r in cls.residents
            if r.zone == "Zone B" and r.hearing_impairment and not r.voice_usable
        ]
        cls.signage_cases = [
            r for r in cls.residents
            if r.zone == "Zone B" and r.visual_impairment and not r.signage_readable
        ]

    def test_master_population_and_ev02_groups(self):
        self.assertEqual(len(self.residents), 1000)
        self.assertEqual(len(self.by_id), 1000)
        self.assertEqual(len(self.voice_cases), 30)
        self.assertEqual(len(self.signage_cases), 20)
        self.assertEqual(
            len({r.resident_id for r in self.voice_cases + self.signage_cases}), 48
        )
        self.assertEqual(
            {r.resident_id for r in self.voice_cases} &
            {r.resident_id for r in self.signage_cases},
            {"R0002", "R0814"},
        )

    def test_all_ev02_cases_across_four_stages(self):
        checks = 0
        for channel, cases in (
            (ChannelID.VOICE_CALL, self.voice_cases),
            (ChannelID.DIGITAL_SIGNAGE, self.signage_cases),
        ):
            for resident in cases:
                for stage in EventStage:
                    with self.subTest(resident=resident.resident_id, channel=channel, stage=stage):
                        result = assess_accessibility_barrier(resident, channel, stage)
                        expected = (BarrierStatus.UNKNOWN if stage in
                                    (EventStage.T00, EventStage.T02) else BarrierStatus.ACTIVE_EV02)
                        self.assertEqual(result.status, expected)
                        self.assertEqual(result.confirmed_barrier, expected == BarrierStatus.ACTIVE_EV02)
                        self.assertFalse(result.confirmed_usable)
                        self.assertIn("BL-01 / EV02", result.evidence)
                        checks += 1
        self.assertEqual(checks, 200)

    def test_outside_zone_b_no_origin_invention(self):
        populations = (
            (ChannelID.VOICE_CALL, [r for r in self.residents if r.zone != "Zone B"
                                    and r.hearing_impairment and not r.voice_usable], 35),
            (ChannelID.DIGITAL_SIGNAGE, [r for r in self.residents if r.zone != "Zone B"
                                         and r.visual_impairment and not r.signage_readable], 28),
        )
        for channel, people, expected in populations:
            self.assertEqual(len(people), expected)
            for resident in people:
                for stage in EventStage:
                    with self.subTest(resident=resident.resident_id, channel=channel, stage=stage):
                        assessment = assess_accessibility_barrier(resident, channel, stage)
                        self.assertEqual(assessment.status, BarrierStatus.UNKNOWN)
                        self.assertFalse(assessment.confirmed_barrier)
                        self.assertFalse(assessment.confirmed_usable)

    def test_no_recorded_barrier_does_not_mean_confirmed_usable(self):
        # A Yes flag is only evidence for one channel-specific attribute.
        sample = next(r for r in self.residents if r.voice_usable)
        for stage in EventStage:
            result = assess_accessibility_barrier(sample, ChannelID.VOICE_CALL, stage)
            self.assertEqual(result.status, BarrierStatus.NO_RECORDED_BARRIER)
            self.assertFalse(result.confirmed_usable)

    def test_unrelated_channels_are_not_assessed(self):
        resident = self.by_id["R0002"]
        for channel in (ChannelID.SMS, ChannelID.MOBILE_APP, ChannelID.PUBLIC_SIRENS):
            for stage in EventStage:
                result = assess_accessibility_barrier(resident, channel, stage)
                self.assertEqual(result.status, BarrierStatus.NOT_ASSESSED)
                self.assertFalse(result.confirmed_usable)

    def test_invalid_inputs_are_rejected(self):
        resident = self.by_id["R0002"]
        with self.assertRaises(TypeError):
            assess_accessibility_barrier(None, ChannelID.VOICE_CALL, EventStage.T04)
        with self.assertRaises(TypeError):
            assess_accessibility_barrier(resident, "CH03", EventStage.T04)
        with self.assertRaises(TypeError):
            assess_accessibility_barrier(resident, ChannelID.VOICE_CALL, "T+04:00")

    def test_disabled_sms_does_not_change_ev02_assessment(self):
        # Demonstrates independence from planner enabled-channel set.
        resident = self.by_id["R0002"]
        with_sms = SimulationConfiguration(EventStage.T04, tuple(ChannelID))
        without_sms = SimulationConfiguration(
            EventStage.T04, tuple(ch for ch in ChannelID if ch != ChannelID.SMS)
        )
        self.assertNotIn(ChannelID.SMS, without_sms.enabled_channels)
        self.assertIn(ChannelID.SMS, with_sms.enabled_channels)
        for channel in (ChannelID.VOICE_CALL, ChannelID.DIGITAL_SIGNAGE):
            a = assess_accessibility_barrier(resident, channel, with_sms.selected_stage)
            b = assess_accessibility_barrier(resident, channel, without_sms.selected_stage)
            self.assertEqual(a, b)
            self.assertEqual(a.status, BarrierStatus.ACTIVE_EV02)
        # Note: this does NOT establish integrated delivery/recovery behavior.

    def test_determinism_and_source_profiles_unchanged(self):
        resident = self.by_id["R0002"]
        before = resident
        one = assess_accessibility_barrier(resident, ChannelID.VOICE_CALL, EventStage.T04)
        two = assess_accessibility_barrier(resident, ChannelID.VOICE_CALL, EventStage.T04)
        self.assertEqual(one, two)
        self.assertEqual(resident, before)


if __name__ == "__main__":
    unittest.main()
