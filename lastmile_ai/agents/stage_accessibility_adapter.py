"""Salma's review-only EV02 adapter proposal.

Does NOT edit the original Agents, simulated residents, or channel eligibility.
Can be wired into Agent 3 and Agent 4 after Sirin reviews Ethar's resolver.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Any, Callable, Mapping

from lastmile_ai.schemas import (
    AccessibilityStatus, Agent3Output, ChannelID, EventStage,
    EvidenceKind, EvidenceReference, RecoveryCandidate,
)

BARRIER = 'Barrier'
UNKNOWN = 'Unknown'
NO_KNOWN = 'NoKnownBarrier'
VALID = {BARRIER, UNKNOWN, NO_KNOWN}


@dataclass(frozen=True)
class BarrierDecision:
    """Normalized EV02 assessment for one resident and channel."""
    resident_id: str
    stage: EventStage
    channel_id: ChannelID
    barrier_status: str
    barrier_origin: str
    reason: str
    evidence_refs: tuple[str, ...]


def normalize_assessment(raw: Mapping[str, Any] | Any, *, resident_id: str,
                         stage: EventStage, channel_id: ChannelID) -> BarrierDecision:
    """Reject mismatched or fabricated assessments."""
    def value(k):
        return raw.get(k) if isinstance(raw, Mapping) else getattr(raw, k, None)
    st = value('stage')
    ch = value('channel_id')
    if isinstance(st, EventStage): st = st.value
    if isinstance(ch, ChannelID): ch = ch.value
    if (value('schema_version') != 'ev02_barrier.v1'
        or value('resident_id') != resident_id or st != stage.value
        or ch != channel_id.value or value('barrier_status') not in VALID):
        raise ValueError('EV02 assessment does not match the required resident/stage/channel contract')
    origin = value('barrier_origin')
    if origin not in ('Permanent', 'EV02', 'None', 'Undetermined'):
        raise ValueError('Invalid barrier origin')
    reason = value('reason')
    refs = value('evidence_refs')
    if not isinstance(reason, str) or not reason.strip() or not isinstance(refs, (tuple,list)):
        raise ValueError('EV02 assessment requires reason and evidence_refs')
    if any(not isinstance(ref,str) or not ref.strip() for ref in refs):
        raise ValueError('Invalid evidence_refs')
    if value('barrier_status') == BARRIER and not refs:
        raise ValueError('Confirmed barrier must have traceable evidence')
    if origin == 'EV02' and stage in (EventStage.T00, EventStage.T02) and value('barrier_status') == BARRIER:
        raise ValueError('EV02-only barrier cannot be activated before T+04')
    return BarrierDecision(resident_id,stage,channel_id,value('barrier_status'),origin,reason,tuple(refs))


def adapt_agent3_stage(output: Agent3Output, stage: EventStage,
                       resolver: Callable[[str, EventStage, ChannelID], Any]) -> Agent3Output:
    """Conservatively overlay verified EV02 findings; never create usability."""
    updated=[]
    for finding in output.accessibility_findings:
        if finding.channel_id not in (ChannelID.VOICE_CALL,ChannelID.DIGITAL_SIGNAGE) or finding.status is AccessibilityStatus.NOT_ASSESSED:
            updated.append(finding)
            continue
        raw=resolver(finding.resident_id, stage, finding.channel_id)
        decision=normalize_assessment(raw,resident_id=finding.resident_id,
                                      stage=stage,channel_id=finding.channel_id)
        # NoKnownBarrier is NOT confirmation of USABLE: preserve original
        # Agent 3 content/rendering decision, but cannot rescue an original
        # profile-derived barrier without re-evaluating the original source.
        if decision.barrier_status == NO_KNOWN:
            updated.append(finding)
            continue
        status=AccessibilityStatus.BARRIER if decision.barrier_status == BARRIER else AccessibilityStatus.REVIEW
        extra=tuple(EvidenceReference(ref,decision.reason,EvidenceKind.SIMULATION_RECORD)
                    for ref in decision.evidence_refs)
        updated.append(replace(finding,status=status,actionable=False if status is AccessibilityStatus.BARRIER else None,
                               reason=f'{decision.reason} [EV02 stage assessment]', evidence=finding.evidence+extra))
    return replace(output,accessibility_findings=tuple(updated))


def review_recovery_assignments(candidate: RecoveryCandidate, stage: EventStage,
                                resolver: Callable[[str, EventStage, ChannelID], Any]) -> dict[str, tuple[str, ...]]:
    """Classify existing proposed assignments, leaving plan and eligibility untouched."""
    blocked=[]; review=[]
    for assignment in candidate.assignments:
        ch=assignment.selected_channel
        if ch not in (ChannelID.VOICE_CALL,ChannelID.DIGITAL_SIGNAGE):
            continue
        decision=normalize_assessment(resolver(assignment.resident_id,stage,ch),
                                      resident_id=assignment.resident_id,stage=stage,channel_id=ch)
        if decision.barrier_status == BARRIER:
            blocked.append(assignment.resident_id)
        elif decision.barrier_status == UNKNOWN:
            review.append(assignment.resident_id)
    return {'blocked':tuple(blocked),'review_required':tuple(review)}
