"""Agent 2 — technical risk analysis for LastMile AI Step 3.

Uses only actually selected delivery records to assign risk. Potential evaluations
are deliberately excluded. Accessibility review is a distinct evidence-based flag,
not a modifier of technical priority.
"""
from __future__ import annotations

from collections import defaultdict

from lastmile_ai.schemas import (
    Agent2Input, Agent2Output, AssignmentStatus, ChannelID,
    DeliveryStatus, EvidenceKind, EvidenceReference,
    ResidentRiskFinding, RiskPriority,
)

ARRIVAL_STATUSES = frozenset((DeliveryStatus.DELIVERED, DeliveryStatus.DELAYED))


def analyze_risk(agent_input: Agent2Input) -> Agent2Output:
    """Assess every resident under the input plan and validate the handoff."""
    if not isinstance(agent_input, Agent2Input):
        raise TypeError("analyze_risk requires Agent2Input")

    delivery = agent_input.delivery_results
    plan_id = delivery.plan_id
    records_by_resident = defaultdict(list)
    for record in delivery.selected_delivery_records:
        records_by_resident[record.resident_id].append(record)

    assignments = {a.resident_id: a for a in agent_input.agent1_input.assignments}
    findings = []
    for resident in agent_input.agent1_input.residents:
        resident_id = resident.resident_id
        selected = records_by_resident[resident_id]
        assignment = assignments[resident_id]
        arrived = [r for r in selected if r.attempted and r.status in ARRIVAL_STATUSES]

        if any(r.status == DeliveryStatus.DELIVERED for r in arrived):
            priority = RiskPriority.LOW
            reason = "At least one selected warning arrived within 30 seconds."
        elif arrived:
            priority = RiskPriority.MEDIUM
            reason = "Selected warning arrived after 30 seconds but within 60 seconds."
        elif assignment.assignment_status == AssignmentStatus.NO_ELIGIBLE_CHANNEL:
            priority = RiskPriority.HIGH
            reason = "No eligible planner-enabled channel was assigned; no arrival."
        else:
            priority = RiskPriority.HIGH
            reason = "No selected-channel warning arrived within 60 seconds."

        # Known selected-channel usability barriers only. Do not infer a barrier
        # from diagnosis alone, weak connectivity, or unselected alternatives.
        barriers = []
        for r in selected:
            if r.channel_id == ChannelID.VOICE_CALL and not resident.voice_usable:
                barriers.append("Selected voice call is not usable per resident profile")
            if r.channel_id == ChannelID.DIGITAL_SIGNAGE and not resident.signage_readable:
                barriers.append("Selected digital signage is not readable per resident profile")
        review = bool(barriers)

        evidence = [EvidenceReference(
            reference_id=f"{plan_id}:{resident_id}:SELECTED_DELIVERY",
            description=(
                f"Selected actual outcomes: "
                + (", ".join(f"{r.channel_id.value}={r.status.value}"
                             for r in selected) if selected else "none")
                + f"; assignment={assignment.assignment_status.value}."
            ),
            kind=EvidenceKind.SIMULATION_RECORD,
        )]
        if barriers:
            evidence.append(EvidenceReference(
                reference_id=f"{plan_id}:{resident_id}:ACCESSIBILITY_PROFILE",
                description="; ".join(dict.fromkeys(barriers)),
                kind=EvidenceKind.SCENARIO_ASSUMPTION,
            ))
        findings.append(ResidentRiskFinding(
            resident_id=resident_id,
            priority=priority,
            reason=reason,
            accessibility_review_needed=review,
            evidence=tuple(evidence),
        ))

    result = Agent2Output(plan_id=plan_id, resident_risks=tuple(findings))
    result.validate_against_input(agent_input, require_complete=True)
    return result


# Explicit callable alias for simple pipeline integration.
run_agent2 = analyze_risk
