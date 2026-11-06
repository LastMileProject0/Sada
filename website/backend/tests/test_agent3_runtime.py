"""Focused Agent 3 runtime tests using Step 2 schema contracts and fixed Arabic content."""
import unittest
from lastmile_ai.schemas import (
    SimulationConfiguration, EventStage, ChannelID, ResidentProfile,
    Agent1Input, Agent1Output, PlanAssignment, AssignmentStatus, DeliveryRecord,
    DeliveryStatus, Agent2Output, RiskPriority, ResidentRiskFinding, EvidenceReference,
    EvidenceKind, Agent3Input, AccessibilityStatus, PolicyCheckStatus,
)
from lastmile_ai.agents.evaluation import evaluate_content, ContentStatus
from lastmile_ai.agents.policy_accessibility import assess_agent3, load_knowledge, FIXTURE_ID, RULES_ID, REGISTRY_ID

FIXTURE, REGISTRY = load_knowledge()


def run_one(channel, *, arrived=True, delayed=False, voice_usable=True, signage_readable=True,
            stage=EventStage.T00, rendering=None):
    profile = ResidentProfile('R0001','Zone B',30,False,False,False,False,False,
                             True,True,True,False,voice_usable,signage_readable,False)
    config = SimulationConfiguration(stage,(channel,))
    assignment = PlanAssignment('R0001','P0',AssignmentStatus.ASSIGNED,channel,'Selected')
    a1 = Agent1Input(config,(profile,),(assignment,))
    status = (DeliveryStatus.FAILED if not arrived else
              DeliveryStatus.DELAYED if delayed else DeliveryStatus.DELIVERED)
    rec = DeliveryRecord('R0001','P0',channel,status,True,True,0,
                         None if not arrived else (40 if delayed else 10), 'Synthetic delivery', 'SIM')
    delivered = Agent1Output('P0',(rec,),(),())
    evidence = (EvidenceReference('SIM','Synthetic risk',EvidenceKind.SIMULATION_RECORD),)
    priority = RiskPriority.HIGH if not arrived else RiskPriority.MEDIUM if delayed else RiskPriority.LOW
    a2 = Agent2Output('P0',(ResidentRiskFinding('R0001',priority,'Synthetic',False,evidence),))
    a3 = Agent3Input(config,a1,delivered,a2,FIXTURE_ID,RULES_ID,REGISTRY_ID)
    ev = {} if rendering is None else {('R0001',channel.value): rendering}
    return assess_agent3(a3, fixture=FIXTURE, registry=REGISTRY, rendering_evidence=ev)


class Agent3RuntimeTests(unittest.TestCase):
    def test_sms_unknown_segments_needs_review(self):
        finding = run_one(ChannelID.SMS, rendering={'format_usable':True}).accessibility_findings[0]
        self.assertEqual(finding.status, AccessibilityStatus.REVIEW)
        self.assertIsNone(finding.actionable)

    def test_sms_complete_and_usable(self):
        finding = run_one(ChannelID.SMS, rendering={'complete_rendering_received':True,'format_usable':True}).accessibility_findings[0]
        self.assertEqual(finding.status, AccessibilityStatus.USABLE)
        self.assertTrue(finding.actionable)

    def test_no_assumed_app_accessibility(self):
        finding = run_one(ChannelID.MOBILE_APP).accessibility_findings[0]
        self.assertEqual(finding.status, AccessibilityStatus.REVIEW)

    def test_app_with_explicit_usable_evidence(self):
        finding = run_one(ChannelID.MOBILE_APP,rendering={'format_usable':True}).accessibility_findings[0]
        self.assertEqual(finding.status, AccessibilityStatus.USABLE)
        self.assertTrue(finding.actionable)

    def test_voice_barrier(self):
        finding = run_one(ChannelID.VOICE_CALL, voice_usable=False).accessibility_findings[0]
        self.assertEqual(finding.status, AccessibilityStatus.BARRIER)
        self.assertFalse(finding.actionable)

    def test_voice_tts_unconfirmed(self):
        finding = run_one(ChannelID.VOICE_CALL).accessibility_findings[0]
        self.assertEqual(finding.status, AccessibilityStatus.REVIEW)

    def test_voice_tts_confirmed(self):
        finding = run_one(ChannelID.VOICE_CALL,rendering={'audio_playback_completed':True}).accessibility_findings[0]
        self.assertTrue(finding.actionable)

    def test_siren_never_actionable(self):
        finding = run_one(ChannelID.PUBLIC_SIRENS).accessibility_findings[0]
        self.assertIsNot(finding.actionable, True)
        self.assertEqual(evaluate_content(ChannelID.PUBLIC_SIRENS,FIXTURE).status, ContentStatus.INSUFFICIENT)

    def test_signage_known_barrier(self):
        finding = run_one(ChannelID.DIGITAL_SIGNAGE,signage_readable=False).accessibility_findings[0]
        self.assertEqual(finding.status, AccessibilityStatus.BARRIER)

    def test_signage_usable(self):
        finding = run_one(ChannelID.DIGITAL_SIGNAGE).accessibility_findings[0]
        self.assertTrue(finding.actionable)

    def test_failed_not_assessed(self):
        finding = run_one(ChannelID.SMS,arrived=False).accessibility_findings[0]
        self.assertEqual(finding.status, AccessibilityStatus.NOT_ASSESSED)
        self.assertIsNone(finding.actionable)

    def test_delayed_does_not_change_content_verdict(self):
        finding = run_one(ChannelID.DIGITAL_SIGNAGE,delayed=True).accessibility_findings[0]
        self.assertTrue(finding.actionable)
        # Arrival timeliness must be checked separately by Metrics (<= 30 only).

    def test_ev03_reviews_are_separate(self):
        result = run_one(ChannelID.DIGITAL_SIGNAGE,stage=EventStage.T06)
        self.assertEqual({p.check_type for p in result.policy_findings},{'Authorization','Privacy'})
        self.assertTrue(all(p.status == PolicyCheckStatus.REVIEW_REQUIRED for p in result.policy_findings))
        self.assertTrue(result.accessibility_findings[0].actionable)  # no auto-block of internal channels

    def test_source_cap_advisory_only(self):
        result = run_one(ChannelID.SMS)
        self.assertEqual(result.cap_advisory.source_ids,('SRC-01',))
        self.assertFalse(hasattr(result.cap_advisory,'compliant'))

    def test_arabic_fixture_language(self):
        self.assertEqual(FIXTURE['warning']['language'],'ar')
        self.assertEqual(len(FIXTURE['approved_channel_renderings']),5)


if __name__ == '__main__':
    unittest.main()
