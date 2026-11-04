"""Real integration tests: EV02 resolver is opt-in, conservative, read-only."""
import unittest

from lastmile_ai.schemas import (
    AccessibilityStatus, AssignmentStatus, ChannelID, EventStage,
    SimulationConfiguration,
)
from lastmile_ai.runtime import run_integrated_baseline
from lastmile_ai.recovery_runtime import run_integrated_recovery
from lastmile_ai.agents.recovery import propose_candidates
from lastmile_ai.pipeline import make_recovery_input
from lastmile_ai.ai.policy_explainer import explain_policy
from lastmile_ai.ai.maymona_rag_bridge import explain_from_maymona


def ev02_fixture(resident_id, stage, channel):
    """Synthetic resolver ONLY; no claim about real EV02 membership."""
    status, origin = 'NoKnownBarrier', 'None'
    refs = ['TEST-FIXTURE-ONLY']
    if resident_id == 'R0001' and channel is ChannelID.DIGITAL_SIGNAGE:
        if stage in (EventStage.T04, EventStage.T06):
            status, origin = 'Barrier', 'EV02'
        else:
            status, origin = 'Unknown', 'EV02'
    return {
        'schema_version': 'ev02_barrier.v1', 'resident_id': resident_id,
        'stage': stage.value, 'channel_id': channel.value,
        'barrier_status': status, 'barrier_origin': origin,
        'reason': 'TEST ONLY: stage-specific signage provenance',
        'evidence_refs': refs,
    }


class RealStageWiringTests(unittest.TestCase):
    def test_no_resolver_keeps_approved_p0_metrics(self):
        config = SimulationConfiguration(EventStage.T02, (ChannelID.DIGITAL_SIGNAGE,))
        first = run_integrated_baseline(config)
        again = run_integrated_baseline(config, stage_barrier_resolver=None)
        self.assertEqual(first.metrics, again.metrics)
        self.assertEqual(first.accessibility, again.accessibility)

    def test_unknown_t02_never_upgrades_or_increases_coverage(self):
        config = SimulationConfiguration(EventStage.T02, (ChannelID.DIGITAL_SIGNAGE,))
        original = run_integrated_baseline(config)
        staged = run_integrated_baseline(config, stage_barrier_resolver=ev02_fixture)
        match = [f for f in staged.accessibility.accessibility_findings if f.resident_id == 'R0001']
        self.assertEqual(len(match), 1)
        self.assertIs(match[0].status, AccessibilityStatus.REVIEW)
        self.assertIsNone(match[0].actionable)
        self.assertLessEqual(staged.metrics.effective_coverage_count, original.metrics.effective_coverage_count)
        self.assertEqual(staged.agent1_input.assignments, original.agent1_input.assignments)
        self.assertEqual(staged.delivery, original.delivery)

    def test_ev02_t04_is_barrier_not_retroactively_t02(self):
        for stage, expected in ((EventStage.T02, AccessibilityStatus.REVIEW),
                                (EventStage.T04, AccessibilityStatus.BARRIER),
                                (EventStage.T06, AccessibilityStatus.BARRIER)):
            config = SimulationConfiguration(stage, (ChannelID.DIGITAL_SIGNAGE,))
            staged = run_integrated_baseline(config, stage_barrier_resolver=ev02_fixture)
            finding = next(f for f in staged.accessibility.accessibility_findings if f.resident_id == 'R0001')
            self.assertIs(finding.status, expected)
            self.assertNotEqual(finding.actionable, True)

    def test_real_recovery_reruns_with_resolver_and_keeps_kpis_consistent(self):
        config = SimulationConfiguration(EventStage.T04, tuple(ChannelID))
        run = run_integrated_recovery(config, stage_barrier_resolver=ev02_fixture)
        self.assertTrue(run.recovery.recommended_plan_id in {'P0','P1','P2','P3'})
        self.assertEqual(run.baseline.metrics, run.recovery.baseline_metrics)
        self.assertEqual(len(run.tested_plans), 3)
        for plan in run.tested_plans:
            for finding in plan.accessibility.accessibility_findings:
                if finding.resident_id == 'R0001' and finding.channel_id == ChannelID.DIGITAL_SIGNAGE:
                    self.assertIs(finding.status, AccessibilityStatus.BARRIER)
            self.assertGreaterEqual(plan.metrics.estimated_reach_count, plan.metrics.effective_coverage_count)
        for candidate in run.recovery.candidates:
            for assignment in candidate.assignments:
                if assignment.resident_id == 'R0001':
                    self.assertNotEqual(assignment.selected_channel, ChannelID.DIGITAL_SIGNAGE)

    def test_unknown_technically_eligible_not_false_no_eligible(self):
        config = SimulationConfiguration(EventStage.T02, (ChannelID.DIGITAL_SIGNAGE,))
        baseline = run_integrated_baseline(config, stage_barrier_resolver=ev02_fixture)
        props = propose_candidates(make_recovery_input(baseline), baseline.agent1_input.assignments,
                                   frozenset(), stage_barrier_resolver=ev02_fixture)
        for plan in props:
            r1 = next(a for a in plan.assignments if a.resident_id == 'R0001')
            self.assertEqual(r1.assignment_status, AssignmentStatus.ASSIGNED)
            self.assertEqual(r1.selected_channel, ChannelID.DIGITAL_SIGNAGE)


class FinalRagPromptTests(unittest.TestCase):
    def test_prompt_lists_only_real_passage_ids(self):
        data = {'schema_version':'policy_retrieval.v1','query':'Q', 'method':'lexical',
                'passages':[{'passage_id':'SRC-01-E01','source_id':'SRC-01',
                   'source_title':'Common Alerting Protocol (CAP) Version 1.2',
                   'section':'§3.2.2 instruction (OPTIONAL)',
                   'locator':'Official HTML section §3.2.2',
                   'source_verified':True,
                   'official_url':'https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html',
                   'text':'The text describing the recommended action to be taken by recipients of the alert message (OPTIONAL)'}]}
        prompt_seen = []
        def model(prompt, model_id):
            prompt_seen.append(prompt)
            return 'حقل instruction يصف الإجراء الموصى به وهو اختياري في CAP 1.2. [SRC-01-E01]'
        result = explain_policy('ما وظيفة حقل instruction وهل هو اختياري؟', data, provider=model)
        self.assertEqual(result.status, 'Answered', result.limitations)
        self.assertEqual(result.citations[0]['passage_id'], 'SRC-01-E01')
        self.assertIn('ONLY allowed citation IDs', prompt_seen[0])
        self.assertIn('Never write [PASSAGE_ID]', prompt_seen[0])

    def test_unknown_passage_marker_never_accepted(self):
        result = explain_from_maymona('ما وظيفة حقل instruction في CAP 1.2؟',
            provider=lambda *_:'الحقل اختياري وفق [text في PASSAGE-01-E01].')
        self.assertEqual(result.status, 'ReviewRequired')
        self.assertEqual(result.citations, ())


if __name__ == '__main__':
    unittest.main()

class CitationRetryTests(unittest.TestCase):
    def test_invented_citation_regenerated_not_silently_replaced(self):
        """A newly generated valid reference may pass, not the invalid one."""
        data = {'schema_version':'policy_retrieval.v1', 'query':'Q', 'method':'lexical',
                'passages':[{'passage_id':'SRC-01-E01', 'source_id':'SRC-01',
                  'source_title':'CAP Version 1.2', 'section':'instruction optional',
                  'locator':'§3.2.2', 'source_verified':True,
                  'official_url':'https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html',
                  'text':'Recommended action (OPTIONAL)'}]}
        replies = iter(['It is optional. [FAKE999]', 'The recommended action is optional. [SRC-01-E01]'])
        attempts = []
        def model(prompt, _model):
            attempts.append(prompt)
            return next(replies)
        result = explain_policy('Q', data, provider=model)
        self.assertEqual(result.status, 'Answered')
        self.assertEqual(result.citations[0]['passage_id'], 'SRC-01-E01')
        self.assertEqual(len(attempts), 2)
        self.assertIn('FORMAT CORRECTION ONLY', attempts[1])

    def test_invented_id_twice_remains_rejected(self):
        """Never manufacture a citation when the model repeats an unknown ID."""
        data = {'schema_version':'policy_retrieval.v1', 'query':'Q', 'method':'lexical',
                'passages':[{'passage_id':'SRC-01-E01', 'source_id':'SRC-01',
                  'source_title':'CAP Version 1.2', 'section':'instruction optional',
                  'locator':'§3.2.2', 'source_verified':True,
                  'official_url':'https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html',
                  'text':'Recommended action (OPTIONAL)'}]}
        result = explain_policy('Q', data, provider=lambda *_:'Made up. [FAKE999]')
        self.assertEqual(result.status, 'ReviewRequired')
        self.assertEqual(result.citations, ())
