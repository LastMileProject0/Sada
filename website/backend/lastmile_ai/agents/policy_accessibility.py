"""LastMile AI Agent 3: policy and accessibility assessment (Step 3).

Uses Salma's unchanged contracts, Sirin-approved Arabic warning, and documented
synthetic profile rules. No CAP validator and no legal-compliance verdicts.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping, Callable
from lastmile_ai.schemas import (
    Agent3Input, Agent3Output, AccessibilityFinding, AccessibilityStatus,
    PolicyFinding, PolicyCheckStatus, CAPAdvisory, EvidenceReference, EvidenceKind,
    ChannelID, DeliveryStatus, EventStage,
)
from .evaluation import evaluate_content, ContentStatus

_ROOT = Path(__file__).resolve().parents[1] / 'knowledge'
FIXTURE_ID = 'ALWADI-FLOOD-EXERCISE-001'
RULES_ID = 'channel_actionability.md'
REGISTRY_ID = 'sources_registry'


def load_knowledge(fixture_path: str | Path | None = None,
                   registry_path: str | Path | None = None) -> tuple[dict, dict]:
    fixture = json.loads(Path(fixture_path or _ROOT / 'warning_fixture.json').read_text(encoding='utf-8'))
    registry = json.loads(Path(registry_path or _ROOT / 'sources_registry.json').read_text(encoding='utf-8'))
    if fixture['warning']['language'] != 'ar' or len(fixture['approved_channel_renderings']) != 5:
        raise ValueError('Approved Arabic five-channel fixture required')
    if {s['id'] for s in registry['sources']} != {f'SRC-0{i}' for i in range(1, 6)}:
        raise ValueError('Five approved core sources required')
    return fixture, registry


def _evidence(ref: str, desc: str, kind: EvidenceKind) -> EvidenceReference:
    return EvidenceReference(reference_id=ref, description=desc, kind=kind)


def assess_agent3(inputs: Agent3Input, *, fixture: Mapping[str, Any] | None = None,
                  registry: Mapping[str, Any] | None = None,
                  rendering_evidence: Mapping[tuple[str, str], Mapping[str, bool | None]] | None = None,
                  stage_barrier_resolver: Callable[..., Any] | None = None) -> Agent3Output:
    """Return policy/accessibility findings for selected attempts only.

    Rendering evidence keys: (resident_id, channel_id) ->
      {'complete_rendering_received': bool|None, 'audio_playback_completed': bool|None,
       'format_usable': bool|None}
    Explicit per-person text/app usability is unknown by default; we NEVER infer
    it solely from disability labels. Renders are fixed across plans/stages.
    """
    if fixture is None or registry is None:
        loaded_fixture, loaded_registry = load_knowledge()
        fixture = fixture if fixture is not None else loaded_fixture
        registry = registry if registry is not None else loaded_registry
    if inputs.warning_fixture_id not in (fixture['warning']['id'], 'warning_fixture.json'):
        raise ValueError('Agent3 warning_fixture_id does not refer to approved warning')
    if inputs.actionability_rules_id not in (RULES_ID, 'channel_actionability'):
        raise ValueError('Agent3 actionability_rules_id mismatch')
    if inputs.source_registry_id not in (REGISTRY_ID, 'sources_registry.json'):
        raise ValueError('Agent3 source_registry_id mismatch')
    if {s['id'] for s in registry['sources']} != {f'SRC-0{i}' for i in range(1, 6)}:
        raise ValueError('Source registry is not the five-source approved inventory')
    residents = {r.resident_id: r for r in inputs.agent1_input.residents}
    records = inputs.delivery_results.selected_delivery_records
    evidence_map = rendering_evidence or {}
    findings = []
    for record in records:
        person = residents[record.resident_id]
        ev = evidence_map.get((record.resident_id, record.channel_id.value), {})
        base = [_evidence('DELIVERY-'+record.resident_id, record.reason, EvidenceKind.SIMULATION_RECORD),
                _evidence(FIXTURE_ID, 'Fixed Arabic warning content and channel rendering', EvidenceKind.SCENARIO_ASSUMPTION)]
        if not record.attempted or record.status not in (DeliveryStatus.DELIVERED, DeliveryStatus.DELAYED):
            findings.append(AccessibilityFinding(record.resident_id, record.channel_id,
                AccessibilityStatus.NOT_ASSESSED, 'No selected channel arrival within the 60-second observation window.',
                None, tuple(base)))
            continue
        content = evaluate_content(record.channel_id, fixture,
            complete_rendering_received=ev.get('complete_rendering_received'),
            audio_playback_completed=ev.get('audio_playback_completed'))
        if record.channel_id is ChannelID.VOICE_CALL:
            usable = person.voice_usable
        elif record.channel_id is ChannelID.DIGITAL_SIGNAGE:
            usable = person.signage_readable
        elif record.channel_id is ChannelID.PUBLIC_SIRENS:
            usable = None  # no recorded individual audibility field
        else:
            usable = ev.get('format_usable')  # never inferred from impairment label
        if usable is False:
            status, actionable, reason = AccessibilityStatus.BARRIER, False, 'Recorded resident/channel presentation barrier.'
        elif usable is None:
            status, actionable, reason = AccessibilityStatus.REVIEW, None, 'Individual presentation usability lacks documented evidence.'
        elif content.status == ContentStatus.REVIEW:
            status, actionable, reason = AccessibilityStatus.REVIEW, None, content.reason
        elif content.status == ContentStatus.INSUFFICIENT:
            status, actionable, reason = AccessibilityStatus.USABLE, False, content.reason
        else:
            status, actionable, reason = AccessibilityStatus.USABLE, True, content.reason
        findings.append(AccessibilityFinding(record.resident_id, record.channel_id, status, reason,
            actionable, tuple(base + [_evidence('CONTENT-'+record.channel_id.value, content.reason,
                                                    EvidenceKind.SCENARIO_ASSUMPTION)])))
    # A No Eligible Channel resident has no selected delivery record; report explicitly.
    selected_residents = {rec.resident_id for rec in records}
    for assignment in inputs.delivery_results.no_eligible_assignments:
        if assignment.resident_id not in selected_residents:
            findings.append(AccessibilityFinding(assignment.resident_id, None,
                AccessibilityStatus.NOT_ASSESSED, 'No Eligible Channel; no selected delivery attempt.', None,
                (_evidence('ASSIGNMENT-'+assignment.resident_id, assignment.reason,
                           EvidenceKind.SIMULATION_RECORD),)))
    ev03 = inputs.configuration.selected_stage is EventStage.T06
    # EV03 pertains ONLY to the excluded hypothetical external channel, never to the
    # five internal CH01–CH05 routes. Explicit review findings are advisory context.
    if ev03:
        auth_status = privacy_status = PolicyCheckStatus.REVIEW_REQUIRED
        auth_reason = 'EV03 hypothetical outside channel requires authorization review; route excluded, not a block on internal channels.'
        privacy_reason = 'EV03 hypothetical external sharing of accessibility-sensitive data needs privacy review; no actual sharing.'
        basis = EvidenceKind.SCENARIO_ASSUMPTION
    else:
        auth_status = privacy_status = PolicyCheckStatus.NO_ISSUE
        auth_reason = 'No internal-channel authorization issue identified under fixed synthetic scenario; not legal approval.'
        privacy_reason = 'No real resident data or external transfer in MVP; no modeled internal-channel issue identified.'
        basis = EvidenceKind.SCENARIO_ASSUMPTION
    policies = (
        PolicyFinding('Authorization', auth_status, auth_reason,
            (_evidence('EV03' if ev03 else 'SCENARIO_AUTH', auth_reason, basis),), inputs.delivery_results.plan_id),
        PolicyFinding('Privacy', privacy_status, privacy_reason,
            (_evidence('EV03' if ev03 else 'SCENARIO_PRIV', privacy_reason, basis),
             _evidence('SRC-05', 'UAE personal-data law: applicability requires human assessment.', EvidenceKind.VERIFIED_SOURCE)),
            inputs.delivery_results.plan_id),
    )
    advisory = CAPAdvisory('OASIS CAP 1.2 describes structured alert information; advisory reference only, no validation or legal certification.', ('SRC-01',))
    output = Agent3Output(inputs.delivery_results.plan_id, tuple(findings), policies, advisory)
    output.validate_against_input(inputs)
    if stage_barrier_resolver is not None:
        # Conservative overlay of verified EV02 provenance. Unknown always REVIEW.
        # No known barrier never upgrades an unsupported usability finding.
        from .stage_accessibility_adapter import adapt_agent3_stage
        output = adapt_agent3_stage(output, inputs.configuration.selected_stage,
                                    stage_barrier_resolver)
        output.validate_against_input(inputs)
    return output
