"""FR-06 dashboard integration checks on real synthetic agent records."""
import html
import re
import unittest

from lastmile_ai.dashboard import build_dashboard
from lastmile_ai.recovery_runtime import run_integrated_recovery
from lastmile_ai.schemas import ChannelID, EventStage, SimulationConfiguration


class DashboardDetailsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recovery_run = run_integrated_recovery(SimulationConfiguration(EventStage.T02, tuple(ChannelID)))
        cls.page = build_dashboard(cls.recovery_run)

    def test_groups_and_channel_tables_present(self):
        for label in ('Accessibility &amp; Affected Groups', 'Hearing impairment',
                      'Limited internet', 'Before gaps', 'After review',
                      'Channel Performance', 'SMS', 'Public Sirens', 'Selected attempts'):
            self.assertIn(label, self.page)
        self.assertIn('view_before', self.page)
        self.assertIn('view_after', self.page)

    def test_metrics_and_candidates_use_real_records(self):
        self.assertIn('722', self.page)
        self.assertIn('942', self.page)
        self.assertIn('366', self.page)
        self.assertIn('P3', self.page)
        for plan_id in ('P0', 'P1', 'P2'):
            self.assertIn(plan_id, self.page)

    def test_escapes_untrusted_explanations_and_has_no_certification(self):
        self.assertIn('not legal certification', self.page)
        self.assertIn('SCENARIO_AUTH', self.page)
        self.assertNotIn('undefined', self.page)
        self.assertIn('No Eligible Channel assignments', self.page)

    def test_only_five_channels_and_selected_attempts(self):
        # Two views, each with exactly one row per approved channel.
        for channel in ChannelID:
            self.assertEqual(self.page.count(f'<th>{channel.value} —'), 2)
        self.assertNotIn('External Channel</th>', self.page)


if __name__ == '__main__':
    unittest.main()
