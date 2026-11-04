"""Agent 4 — conservative recovery search and independently verified selection.

The caller (Sirin's pipeline) owns actual reruns of Agents 1 -> 2 -> 3 and
metrics. This module NEVER manufactures simulated deliveries, authorization,
or coverage. The evaluator must return auditable, computed results.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

from lastmile_ai.schemas import (
    Agent4Input, Agent4Output, AssignmentStatus, ChannelID, PlanAssignment,
    PlanMetrics, PolicyCheckStatus, RecoveryCandidate, RecoveryOutcome,
    AccessibilityStatus,
)


@dataclass(frozen=True)
class VerifiedEvaluation:
    """Results computed by an integrated pipeline, NOT forecasts.

    effective_resident_ids: individuals confirmed timely, usable and actionable
    after running delivery, risk and accessibility assessment. Must be complete.
    authorization_status: verified candidate-specific authorization outcome.
    safety_approved: pipeline's independent feasibility/safety decision.
    """
    metrics: PlanMetrics
    effective_resident_ids: frozenset[str]
    authorization_status: PolicyCheckStatus
    safety_approved: bool
    explanation: str

    def __post_init__(self):
        if not isinstance(self.metrics, PlanMetrics):
            raise TypeError('metrics must be PlanMetrics')
        if not isinstance(self.effective_resident_ids, frozenset) or not all(
            isinstance(v, str) and v for v in self.effective_resident_ids
        ):
            raise TypeError('effective_resident_ids must be frozenset[str]')
        if not isinstance(self.authorization_status, PolicyCheckStatus):
            raise TypeError('authorization_status must be PolicyCheckStatus')
        if type(self.safety_approved) is not bool or not isinstance(self.explanation, str) or not self.explanation.strip():
            raise ValueError('Safety decision and explanation required')


# Selected recovery preference permutations; only planner-enabled channels considered.
STRATEGIES = (
    (ChannelID.MOBILE_APP, ChannelID.VOICE_CALL, ChannelID.SMS, ChannelID.DIGITAL_SIGNAGE, ChannelID.PUBLIC_SIRENS),
    (ChannelID.VOICE_CALL, ChannelID.MOBILE_APP, ChannelID.SMS, ChannelID.DIGITAL_SIGNAGE, ChannelID.PUBLIC_SIRENS),
    (ChannelID.DIGITAL_SIGNAGE, ChannelID.MOBILE_APP, ChannelID.VOICE_CALL, ChannelID.SMS, ChannelID.PUBLIC_SIRENS),
)


def _eligible(resident, channel):
    # Hard prerequisites from approved P0; weak coverage is NOT disqualifying.
    return (
        channel == ChannelID.SMS or channel == ChannelID.VOICE_CALL
        or (channel == ChannelID.MOBILE_APP and resident.emergency_app_installed)
        or (channel == ChannelID.PUBLIC_SIRENS and resident.in_siren_area)
        or (channel == ChannelID.DIGITAL_SIGNAGE and resident.in_signage_area)
    )


def _usable_candidate(resident, channel):
    # An explicit known barrier disqualifies this recovery proposal; other
    # accessibility issues are assessed by Agent 3 at verification time.
    return not (
        (channel == ChannelID.VOICE_CALL and not resident.voice_usable)
        or (channel == ChannelID.DIGITAL_SIGNAGE and not resident.signage_readable)
    )


def propose_candidates(value: Agent4Input, baseline_assignments: tuple[PlanAssignment, ...],
                       baseline_effective_ids: frozenset[str],
                       stage_barrier_resolver: Callable[..., Any] | None = None) -> tuple[RecoveryCandidate, ...]:
    """Make at most three P1-P3 proposals; never report untested metrics."""
    if not isinstance(value, Agent4Input):
        raise TypeError('Requires Agent4Input')
    if not isinstance(baseline_effective_ids, frozenset):
        raise TypeError('baseline_effective_ids must be frozenset')
    known = {r.resident_id for r in value.residents}
    baseline = {a.resident_id: a for a in baseline_assignments}
    if set(baseline) != known or any(a.plan_id != 'P0' for a in baseline_assignments):
        raise ValueError('Exactly one P0 assignment per resident required')
    if not baseline_effective_ids <= known:
        raise ValueError('Unknown effective resident')
    enabled = set(value.configuration.enabled_channels)
    proposals = []
    for index, order in enumerate(STRATEGIES, start=1):
        plan_id = f'P{index}'
        assignments = []
        for resident in value.residents:
            previous = baseline[resident.resident_id]
            # Keep baseline channel for residents already effectively covered;
            # pipeline STILL must verify that coverage does not regress.
            if resident.resident_id in baseline_effective_ids:
                channel = previous.selected_channel
            else:
                # With a provenance-aware resolver, do NOT pre-filter CH03/CH05
                # on the static No flag: that flag may represent Unknown before
                # T+04. The resolver decides confirmed barrier vs review.
                options = [ch for ch in order if ch in enabled and
                           _eligible(resident, ch) and
                           (stage_barrier_resolver is not None or
                            _usable_candidate(resident, ch))]
                if stage_barrier_resolver is None:
                    channel = next(iter(options), None)
                else:
                    from .stage_accessibility_adapter import normalize_assessment
                    confirmed = []
                    unknown = []
                    for ch in options:
                        if ch not in (ChannelID.VOICE_CALL, ChannelID.DIGITAL_SIGNAGE):
                            confirmed.append(ch)
                            continue
                        status = normalize_assessment(
                            stage_barrier_resolver(resident.resident_id,
                                                   value.configuration.selected_stage, ch),
                            resident_id=resident.resident_id,
                            stage=value.configuration.selected_stage,
                            channel_id=ch,
                        ).barrier_status
                        if status == 'Barrier':
                            continue  # documented barrier: do not propose this channel
                        if status == 'Unknown':
                            unknown.append(ch)  # preserve technical eligibility; needs review
                        else:
                            confirmed.append(ch)
                    # Unknown is a last-resort TECHNICAL assignment only, never
                    # proof of accessibility. If the ONLY eligible route has a
                    # confirmed barrier, retain that technically eligible route
                    # for auditing (not endorsement); the evaluator marks the
                    # recovery candidate unsafe and cannot recommend it. Do NOT
                    # manufacture a No Eligible Channel status from disability.
                    channel = (next(iter(confirmed), None)
                               or next(iter(unknown), None)
                               or next(iter(options), None))
            assignments.append(PlanAssignment(
                resident_id=resident.resident_id, plan_id=plan_id,
                assignment_status=AssignmentStatus.ASSIGNED if channel else AssignmentStatus.NO_ELIGIBLE_CHANNEL,
                selected_channel=channel,
                reason='Preserve baseline effective assignment' if resident.resident_id in baseline_effective_ids
                       else 'Recovery priority strategy ' + str(index)
                       + ('; stage barrier audit required: cannot recommend confirmed barrier'
                          if (stage_barrier_resolver is not None and channel is not None
                              and channel in (ChannelID.VOICE_CALL, ChannelID.DIGITAL_SIGNAGE)
                              and normalize_assessment(
                                  stage_barrier_resolver(resident.resident_id,
                                                         value.configuration.selected_stage, channel),
                                  resident_id=resident.resident_id,
                                  stage=value.configuration.selected_stage,
                                  channel_id=channel,
                              ).barrier_status == 'Barrier') else ''),
            ))
        proposals.append(RecoveryCandidate(
            plan_id=plan_id, assignments=tuple(assignments), feasible=True,
            authorization_status=PolicyCheckStatus.INSUFFICIENT_INFO,
            reason='Proposal only; authorization, safety and outcomes must be verified by rerun.',
        ))
    return tuple(proposals)


def run_agent4(value: Agent4Input, *, baseline_assignments: tuple[PlanAssignment, ...],
               baseline_effective_ids: frozenset[str],
               evaluate: Callable[[RecoveryCandidate], VerifiedEvaluation] | None = None,
               stage_barrier_resolver: Callable[..., Any] | None = None) -> Agent4Output:
    """Compare actual evaluator results, or retain P0 if verification unavailable.

    Evaluator MUST rerun Agents 1/2/3 at identical fixed conditions and compute
    PlanMetrics including accessible/actionable on-time coverage. Output is
    conservative: unverified or unauthorized candidates are not selectable.
    """
    if not isinstance(value, Agent4Input):
        raise TypeError('Requires Agent4Input')
    known = {r.resident_id for r in value.residents}
    if not isinstance(baseline_effective_ids, frozenset) or not baseline_effective_ids <= known:
        raise ValueError('baseline_effective_ids must be known resident IDs')
    if len(baseline_effective_ids) != value.baseline_metrics.effective_coverage_count:
        raise ValueError('Baseline effective IDs must agree with baseline metrics')
    if evaluate is not None and not callable(evaluate):
        raise TypeError('evaluate must be a callable or None')

    proposals = propose_candidates(value, baseline_assignments, baseline_effective_ids,
                                   stage_barrier_resolver=stage_barrier_resolver)
    tested = []
    eligible = []
    notes = []
    for candidate in proposals:
        if evaluate is None:
            tested.append(candidate)
            continue
        evaluation = evaluate(candidate)
        if not isinstance(evaluation, VerifiedEvaluation):
            raise TypeError('Evaluator must return VerifiedEvaluation')
        m = evaluation.metrics
        if m.plan_id != candidate.plan_id:
            raise ValueError('Evaluator plan ID mismatch')
        if not evaluation.effective_resident_ids <= known:
            raise ValueError('Evaluator returned unknown residents')
        if len(evaluation.effective_resident_ids) != m.effective_coverage_count:
            raise ValueError('Candidate effectiveness roster/count mismatch')
        authorized = evaluation.authorization_status == PolicyCheckStatus.NO_ISSUE
        nonregression = baseline_effective_ids <= evaluation.effective_resident_ids
        improved = m.effective_coverage_count > value.baseline_metrics.effective_coverage_count
        feasible = evaluation.safety_approved and nonregression
        reason = evaluation.explanation
        if not nonregression:
            reason += '; rejected: previously effective residents lost coverage'
        if not authorized:
            reason += '; rejected: authorization not cleared'
        if not evaluation.safety_approved:
            reason += '; rejected: safety/feasibility not approved'
        if not improved:
            reason += '; no improvement over baseline effective coverage'
        admitted = feasible and authorized
        result = RecoveryCandidate(
            plan_id=candidate.plan_id, assignments=candidate.assignments,
            feasible=feasible, authorization_status=evaluation.authorization_status,
            reason=reason, tested_metrics=m if admitted else None,
        )
        tested.append(result)
        if admitted and improved:
            eligible.append(result)
        else:
            notes.append(f'{candidate.plan_id}: {reason}')

    # Approved ranking: higher resolved accessibility first; then fewer
    # unresolved critical residents; then higher coverage; fewer extra
    # selected attempts; stable plan ID. Safety and no-regression are gates.
    chosen = min(eligible, key=lambda c: (
        -c.tested_metrics.resolved_accessibility_gaps,
        c.tested_metrics.unresolved_critical_count,
        -c.tested_metrics.effective_coverage_count,
        max(0, c.tested_metrics.actual_selected_attempts - value.baseline_metrics.actual_selected_attempts),
        c.plan_id,
    )) if eligible else None

    output = Agent4Output(
        outcome=RecoveryOutcome.PLAN_SELECTED if chosen else RecoveryOutcome.NO_SUITABLE_PLAN,
        recommended_plan_id=chosen.plan_id if chosen else 'P0',
        baseline_metrics=value.baseline_metrics,
        candidates=tuple(tested),
        final_metrics=chosen.tested_metrics if chosen else value.baseline_metrics,
        explanation=(f'{chosen.plan_id} chosen from authorized, safe and verified reruns by approved ranking.'
                     if chosen else 'No authorized, safe, verified recovery with increased effective coverage; P0 retained.'),
        unresolved_review_notes=tuple(notes) if evaluate else ('Candidate rerun and authorization verification not supplied.',),
    )
    output.validate_against_input(value)
    return output


# API alias for integration.
plan_recovery = run_agent4
