"""Stage adapter contract tests; no dataset or production Agent files modified."""
import unittest
from lastmile_ai.agents.stage_accessibility_adapter import (
    normalize_assessment, adapt_agent3_stage, review_recovery_assignments
)
from lastmile_ai.schemas import (
    AccessibilityFinding, AccessibilityStatus, Agent3Output, ChannelID, EventStage,
    EvidenceKind, EvidenceReference, RecoveryCandidate, PlanAssignment,
    AssignmentStatus, PolicyCheckStatus,
)


def assessment(resident_id, stage, channel, status, origin='Undetermined', refs=()):
    return dict(schema_version='ev02_barrier.v1', resident_id=resident_id,
                stage=stage.value, channel_id=channel.value,barrier_status=status,
                barrier_origin=origin,reason='Documented synthetic finding',evidence_refs=list(refs))


def finding(status=AccessibilityStatus.USABLE,channel=ChannelID.VOICE_CALL):
    return AccessibilityFinding('R0001',channel,status,'Original assessment',
                                True if status is AccessibilityStatus.USABLE else None,
                                (EvidenceReference('SIM','synthetic',EvidenceKind.SIMULATION_RECORD),))


def output(f):
    return Agent3Output('P0',(f,),(),None)


class StageAccessibilityAdapterTests(unittest.TestCase):
    def test_permanent_barrier_all_stages(self):
        for stage in EventStage:
            def resolve(r,s,c): return assessment(r,s,c,'Barrier','Permanent',('MASTER',))
            result=adapt_agent3_stage(output(finding()),stage,resolve)
            self.assertEqual(result.accessibility_findings[0].status,AccessibilityStatus.BARRIER)
            self.assertFalse(result.accessibility_findings[0].actionable)

    def test_verified_ev02_barrier_not_before_t04(self):
        for stage in (EventStage.T00,EventStage.T02):
            with self.assertRaises(ValueError):
                normalize_assessment(assessment('R0001',stage,ChannelID.VOICE_CALL,'Barrier','EV02',('EV02',)),
                    resident_id='R0001',stage=stage,channel_id=ChannelID.VOICE_CALL)

    def test_ev02_at_and_after_t04(self):
        for stage in (EventStage.T04,EventStage.T06):
            def resolve(r,s,c): return assessment(r,s,c,'Barrier','EV02',('EV02-REC',))
            result=adapt_agent3_stage(output(finding()),stage,resolve)
            self.assertEqual(result.accessibility_findings[0].status,AccessibilityStatus.BARRIER)

    def test_unknown_forces_review_not_usable(self):
        for stage in EventStage:
            def resolve(r,s,c): return assessment(r,s,c,'Unknown')
            result=adapt_agent3_stage(output(finding()),stage,resolve)
            self.assertEqual(result.accessibility_findings[0].status,AccessibilityStatus.REVIEW)
            self.assertIsNone(result.accessibility_findings[0].actionable)

    def test_unknown_not_hard_unavailable(self):
        stage=EventStage.T02
        assignment=PlanAssignment('R0001','P1',AssignmentStatus.ASSIGNED,ChannelID.VOICE_CALL,'Synthetic')
        candidate=RecoveryCandidate('P1',(assignment,),True,PolicyCheckStatus.INSUFFICIENT_INFO,'Proposed')
        def resolve(r,s,c): return assessment(r,s,c,'Unknown')
        flags=review_recovery_assignments(candidate,stage,resolve)
        self.assertEqual(flags['review_required'],('R0001',))
        self.assertEqual(flags['blocked'],())
        self.assertEqual(candidate.assignments[0].assignment_status,AssignmentStatus.ASSIGNED)

    def test_known_barrier_blocks_recovery_review(self):
        assignment=PlanAssignment('R0001','P1',AssignmentStatus.ASSIGNED,ChannelID.DIGITAL_SIGNAGE,'Synthetic')
        candidate=RecoveryCandidate('P1',(assignment,),True,PolicyCheckStatus.INSUFFICIENT_INFO,'Proposed')
        def resolve(r,s,c): return assessment(r,s,c,'Barrier','Permanent',('MASTER',))
        flags=review_recovery_assignments(candidate,EventStage.T02,resolve)
        self.assertEqual(flags['blocked'],('R0001',))

    def test_no_known_barrier_does_not_confirm_usable(self):
        def resolve(r,s,c): return assessment(r,s,c,'NoKnownBarrier','None',('MASTER',))
        result=adapt_agent3_stage(output(finding(AccessibilityStatus.REVIEW)),EventStage.T04,resolve)
        self.assertEqual(result.accessibility_findings[0].status,AccessibilityStatus.REVIEW)

    def test_invalid_source_id_and_channel(self):
        raw=assessment('R0001',EventStage.T04,ChannelID.VOICE_CALL,'Barrier','EV02',('SRC',))
        with self.assertRaises(ValueError):
            normalize_assessment(raw,resident_id='R0002',stage=EventStage.T04,channel_id=ChannelID.VOICE_CALL)
        with self.assertRaises(ValueError):
            normalize_assessment(raw,resident_id='R0001',stage=EventStage.T04,channel_id=ChannelID.DIGITAL_SIGNAGE)

    def test_non_event_channels_untouched(self):
        original=finding(AccessibilityStatus.USABLE,ChannelID.SMS)
        result=adapt_agent3_stage(output(original),EventStage.T04,
            lambda *_: (_ for _ in ()).throw(AssertionError('Resolver not needed')))
        self.assertEqual(result.accessibility_findings[0],original)

    def test_covered_residents_not_upgraded_by_unknown(self):
        base=output(finding())
        def resolve(r,s,c): return assessment(r,s,c,'Unknown')
        after=adapt_agent3_stage(base,EventStage.T02,resolve)
        def count(out): return sum(f.status is AccessibilityStatus.USABLE and f.actionable is True
                                  for f in out.accessibility_findings)
        self.assertLessEqual(count(after),count(base))

if __name__=='__main__': unittest.main()
