"""Real Ethar->Salma stage integration tests; synthetic Master profiles only."""
from __future__ import annotations

import unittest
from lastmile_ai.accessibility_stage import BarrierStatus, assess_accessibility_barrier
from lastmile_ai.agents.ethar_stage_bridge import (
    make_ethar_stage_resolver,
    run_ethar_integrated_baseline,
    run_ethar_integrated_recovery,
)
from lastmile_ai.agents.recovery import propose_candidates
from lastmile_ai.data.resident_adapter import load_resident_profiles
from lastmile_ai.pipeline import make_recovery_input
from lastmile_ai.runtime import run_integrated_baseline
from lastmile_ai.schemas import (
    AccessibilityStatus, AssignmentStatus, ChannelID, DeliveryStatus,
    EventStage, SimulationConfiguration,
)


class EtharSalmaIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.residents = load_resident_profiles()
        cls.by_id = {r.resident_id: r for r in cls.residents}
        cls.resolver = staticmethod(make_ethar_stage_resolver(cls.residents))

    def test_contract_maps_exact_zone_b_ev02_and_not_early(self):
        """Only evidence-backed Zone B EV02 activates at T+04 onward."""
        for channel in (ChannelID.VOICE_CALL, ChannelID.DIGITAL_SIGNAGE):
            for stage in (EventStage.T00, EventStage.T02):
                result = self.resolver('R0002', stage, channel)
                self.assertEqual(result['barrier_status'], 'Unknown')
                self.assertEqual(result['barrier_origin'], 'Undetermined')
                self.assertFalse(result['evidence_refs'])
            for stage in (EventStage.T04, EventStage.T06):
                result = self.resolver('R0002', stage, channel)
                self.assertEqual(result['barrier_status'], 'Barrier')
                self.assertEqual(result['barrier_origin'], 'EV02')
                self.assertIn('MASTER-PROFILE-RULES:BL-01', result['evidence_refs'])

    def test_unresolved_outside_zone_b_remains_unknown_all_stages(self):
        """Never reclassify undocumented permanent barrier provenance."""
        person = next(r for r in self.residents if r.zone != 'Zone B'
                      and r.hearing_impairment and not r.voice_usable)
        for stage in EventStage:
            report = self.resolver(person.resident_id, stage, ChannelID.VOICE_CALL)
            self.assertEqual(report['barrier_status'], 'Unknown')
            self.assertEqual(report['barrier_origin'], 'Undetermined')

    def test_known_yes_does_not_claim_full_usable(self):
        """No recorded barrier is not a claim of complete usability."""
        person = next(r for r in self.residents if r.voice_usable)
        status = assess_accessibility_barrier(person, ChannelID.VOICE_CALL, EventStage.T04)
        self.assertEqual(status.status, BarrierStatus.NO_RECORDED_BARRIER)
        self.assertFalse(status.confirmed_usable)
        mapped = self.resolver(person.resident_id, EventStage.T04, ChannelID.VOICE_CALL)
        self.assertEqual(mapped['barrier_status'], 'NoKnownBarrier')

    def test_bad_resident_and_out_of_scope_channel_rejected(self):
        """Reject invented residents and unsupported channel assessments."""
        with self.assertRaises(ValueError):
            self.resolver('TEST-NOT-REAL', EventStage.T04, ChannelID.VOICE_CALL)
        with self.assertRaises(ValueError):
            self.resolver('R0002', EventStage.T04, ChannelID.SMS)

    def test_all_stages_p0_keeps_delivery_and_never_adds_coverage(self):
        """Stage-aware barriers affect findings, not P0 delivery or KPIs upward."""
        for stage in EventStage:
            with self.subTest(stage=stage):
                config = SimulationConfiguration(stage, tuple(ChannelID))
                original = run_integrated_baseline(config)
                integrated = run_ethar_integrated_baseline(config)
                self.assertEqual(integrated.delivery, original.delivery)
                self.assertEqual(integrated.agent1_input.assignments, original.agent1_input.assignments)
                self.assertLessEqual(integrated.metrics.effective_coverage_count,
                                     original.metrics.effective_coverage_count)

    def test_before_after_t04_agent3_voice_finding(self):
        """Arrived Zone B EV02 voice cases switch REVIEW to BARRIER at T+04."""
        for stage, expected in ((EventStage.T02, AccessibilityStatus.REVIEW),
                                (EventStage.T04, AccessibilityStatus.BARRIER)):
            config = SimulationConfiguration(stage, (ChannelID.VOICE_CALL,))
            result = run_ethar_integrated_baseline(config)
            statuses = {
                (f.resident_id, f.channel_id): f
                for f in result.accessibility.accessibility_findings
            }
            matched = 0
            for r in self.residents:
                if r.zone != 'Zone B' or not r.hearing_impairment or r.voice_usable:
                    continue
                f = statuses.get((r.resident_id, ChannelID.VOICE_CALL))
                if f is None or f.status is AccessibilityStatus.NOT_ASSESSED:
                    continue
                self.assertEqual(f.status, expected)
                self.assertIsNot(f.actionable, True)
                matched += 1
            self.assertGreater(matched, 0)

    def test_unknown_remains_technically_eligible_in_recovery(self):
        """Unknown cannot become a fake No Eligible Channel status."""
        config = SimulationConfiguration(EventStage.T02, (ChannelID.VOICE_CALL,))
        baseline = run_ethar_integrated_baseline(config)
        proposals = propose_candidates(
            make_recovery_input(baseline), baseline.agent1_input.assignments,
            frozenset(), stage_barrier_resolver=self.resolver,
        )
        for p in proposals:
            selected = next(a for a in p.assignments if a.resident_id == 'R0002')
            self.assertEqual(selected.assignment_status, AssignmentStatus.ASSIGNED)
            self.assertEqual(selected.selected_channel, ChannelID.VOICE_CALL)

    def test_no_only_channel_false_no_eligible_or_unsafe_approval(self):
        """A barred-only recovery candidate stays auditable and nonselectable."""
        config = SimulationConfiguration(EventStage.T04, (ChannelID.VOICE_CALL,))
        recovery = run_ethar_integrated_recovery(config)
        for candidate in recovery.recovery.candidates:
            assignment = next(a for a in candidate.assignments if a.resident_id == 'R0002')
            self.assertEqual(assignment.assignment_status, AssignmentStatus.ASSIGNED)
            self.assertIn('stage barrier audit required', assignment.reason)
        self.assertEqual(recovery.recovery.recommended_plan_id, 'P0')
        self.assertTrue(all(not p.modeled_prerequisites_pass for p in recovery.tested_plans))

    def test_recovery_avoids_confirmed_barriers_with_alternatives(self):
        """When other channels exist, proposals never assign confirmed EV02 routes."""
        config = SimulationConfiguration(EventStage.T04, tuple(ChannelID))
        run = run_ethar_integrated_recovery(config)
        for candidate in run.recovery.candidates:
            for assignment in candidate.assignments:
                if assignment.selected_channel not in (ChannelID.VOICE_CALL, ChannelID.DIGITAL_SIGNAGE):
                    continue
                report = self.resolver(assignment.resident_id, EventStage.T04, assignment.selected_channel)
                self.assertNotEqual(report['barrier_status'], 'Barrier')
        self.assertEqual(run.baseline.metrics, run.recovery.baseline_metrics)
        self.assertGreaterEqual(run.recovery.final_metrics.effective_coverage_count,
                                run.recovery.baseline_metrics.effective_coverage_count)

    def test_ai_explanation_cannot_change_ethar_recovery_selection(self):
        """AI is read-only after actual Ethar-aware P0/P1/P2/P3 reruns."""
        from lastmile_ai.ai.maymona_rag_bridge import explain_from_maymona
        config = SimulationConfiguration(EventStage.T04, tuple(ChannelID))
        before = run_ethar_integrated_recovery(config)
        result = explain_from_maymona(
            'ما وظيفة حقل instruction في معيار CAP 1.2؟ وهل هو اختياري؟',
            provider=lambda *_: 'حقل instruction اختياري. [SRC-01-E01]',
        )
        self.assertEqual(result.status, 'Answered')
        after = run_ethar_integrated_recovery(config)
        self.assertEqual(before.recovery.recommended_plan_id,
                         after.recovery.recommended_plan_id)
        self.assertEqual(before.recovery.final_metrics, after.recovery.final_metrics)
        self.assertEqual(before.baseline.delivery, after.baseline.delivery)
        self.assertEqual(
            tuple((p.plan_id, p.assignments, p.tested_metrics) for p in before.recovery.candidates),
            tuple((p.plan_id, p.assignments, p.tested_metrics) for p in after.recovery.candidates),
        )

    def test_sms_disabled_does_not_enable_sms_or_change_baseline(self):
        """SMS-off baseline preserves channel disablement under EV02."""
        enabled = tuple(c for c in ChannelID if c is not ChannelID.SMS)
        config = SimulationConfiguration(EventStage.T02, enabled)
        initial = run_integrated_baseline(config)
        stage_aware = run_ethar_integrated_recovery(config)
        self.assertEqual(initial.delivery, stage_aware.baseline.delivery)
        self.assertTrue(all(
            a.selected_channel is not ChannelID.SMS
            for c in stage_aware.recovery.candidates for a in c.assignments
        ))


if __name__ == '__main__':
    unittest.main()
