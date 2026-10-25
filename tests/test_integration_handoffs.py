"""Independent Step 2 integration checks; NOT agent simulation tests."""
import json
from pathlib import Path
import unittest

from lastmile_ai.data.resident_adapter import load_resident_profiles
from lastmile_ai.schemas import (AccessibilityFinding, AccessibilityStatus,
    ChannelID, DeliveryRecord, DeliveryStatus, EventStage, EvidenceReference,
    EvidenceKind, SimulationConfiguration)

ROOT = Path(__file__).resolve().parents[1]

class TestIntegrationHandoffs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load_resident_profiles()
        cls.sources = json.loads((ROOT/'lastmile_ai/knowledge/sources_registry.json').read_text(encoding='utf-8'))
        cls.warning = json.loads((ROOT/'lastmile_ai/knowledge/warning_fixture.json').read_text(encoding='utf-8'))

    def test_typed_resident_profiles_cover_approved_population(self):
        self.assertEqual(len(self.profiles), 1000)
        self.assertEqual(len({r.resident_id for r in self.profiles}), 1000)
        self.assertEqual(sum(r.emergency_app_installed for r in self.profiles),600)
        self.assertEqual(sum(r.elderly_65_plus for r in self.profiles),150)
        self.assertEqual(sum(r.policy_age_60_plus for r in self.profiles),228)
        self.assertEqual(sum(r.sms_failed_ev01 for r in self.profiles),245)

    def test_warning_matches_contract_channel_ids_and_stages(self):
        self.assertEqual(set(self.warning['approved_channel_renderings']),{c.value for c in ChannelID})
        self.assertEqual(set(self.warning['simulation_policy']['valid_stage_choices']),{s.value for s in EventStage})
        self.assertEqual(self.warning['simulation_policy']['observation_window_seconds'],60)
        self.assertEqual(self.warning['simulation_policy']['on_time_delivery_seconds_max'],30)
        self.assertTrue(self.warning['simulation_policy']['warning_content_fixed_across_stages_and_plans'])
        self.assertFalse(self.warning['approved_channel_renderings']['CH04']['standalone_effective_warning_coverage'])

    def test_sources_use_approved_five_ids(self):
        ids = [s['id'] for s in self.sources['sources']]
        self.assertEqual(ids,['SRC-01','SRC-02','SRC-03','SRC-04','SRC-05'])
        sample=json.loads((ROOT/'docs/examples/agent3_output_example.json').read_text(encoding='utf-8'))
        self.assertEqual(sample['cap_advisory']['source_ids'],['SRC-01'])

    def test_config_example_is_accepted(self):
        data=json.loads((ROOT/'docs/examples/simulation_configuration_example.json').read_text(encoding='utf-8'))
        self.assertEqual(SimulationConfiguration.from_dict(data).selected_stage,EventStage.T00)

    def test_delivery_timing_boundaries(self):
        for sec, expected in ((30,DeliveryStatus.DELIVERED),(31,DeliveryStatus.DELAYED),(60,DeliveryStatus.DELAYED)):
            with self.subTest(arrival_seconds=sec):
                record=DeliveryRecord('R0001','P0',ChannelID.SMS,expected,True,True,0,sec,'synthetic boundary','TEST')
                self.assertEqual(record.status,expected)
        with self.assertRaises(ValueError):
            DeliveryRecord('R0001','P0',ChannelID.SMS,DeliveryStatus.DELIVERED,True,True,0,31,'invalid','TEST')

    def test_public_siren_is_not_actionable(self):
        evidence=(EvidenceReference('fixture','Known siren alert-only rule',EvidenceKind.SCENARIO_ASSUMPTION),)
        with self.assertRaises(ValueError):
            AccessibilityFinding('R0001',ChannelID.PUBLIC_SIRENS,AccessibilityStatus.USABLE,'alert-only',True,evidence)

if __name__=='__main__':
    unittest.main()
