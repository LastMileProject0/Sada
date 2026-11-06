"""Execute Agent 4 candidate reruns using the real LastMile Step 3 agents.

Every P1/P2/P3 candidate is independently tested with the *same* residents,
selected stage, enabled channels, Arabic warning and unknown rendering evidence
as P0. No live alerts, external channels or unverified permissions are used.

This integration does not modify Sirin's metrics/pipeline or team-owned agents.
Agent 4 rejects candidates when scenario policy checks require review; those
checks are synthetic, NOT legal approval for deployment.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any

from lastmile_ai.agents.delivery import run_agent1
from lastmile_ai.agents.policy_accessibility import (
    FIXTURE_ID, REGISTRY_ID, RULES_ID, assess_agent3,
)
from lastmile_ai.agents.recovery import VerifiedEvaluation, run_agent4
from lastmile_ai.agents.risk import run_agent2
from lastmile_ai.agents.scenario_conditions import is_channel_eligible
from lastmile_ai.metrics import (
    count_effective_warning_coverage, count_estimated_reach,
    count_unresolved_critical_cases,
)
from lastmile_ai.pipeline import BaselineResult, make_recovery_input
from lastmile_ai.runtime import run_integrated_baseline
from lastmile_ai.schemas import (
    AccessibilityStatus, Agent1Input, Agent1Output, Agent2Input, Agent2Output,
    Agent3Input, Agent3Output, Agent4Output, AssignmentStatus, ChannelID,
    DeliveryStatus, EventStage, PlanMetrics, PolicyCheckStatus, RecoveryCandidate,
    SimulationConfiguration,
)


@dataclass(frozen=True)
class EvaluatedPlan:
    """Auditable real rerun, including candidates that were not selected."""
    plan_id: str
    delivery: Agent1Output
    risks: Agent2Output
    accessibility: Agent3Output
    metrics: PlanMetrics
    modeled_prerequisites_pass: bool


@dataclass(frozen=True)
class RecoveryRun:
    baseline: BaselineResult
    recovery: Agent4Output
    tested_plans: tuple[EvaluatedPlan, ...]


def effective_resident_ids(delivery: Agent1Output,
                           assessment: Agent3Output) -> frozenset[str]:
    """Use the exact same arrival/accessibility rule as existing metrics.py."""
    if delivery.plan_id != assessment.plan_id:
        raise ValueError('Effective-coverage plans must agree')
    timely = {
        (r.resident_id, r.channel_id)
        for r in delivery.selected_delivery_records
        if r.selected_in_plan and r.attempted and
        r.status == DeliveryStatus.DELIVERED and
        r.channel_id != ChannelID.PUBLIC_SIRENS
    }
    usable = {
        (f.resident_id, f.channel_id)
        for f in assessment.accessibility_findings
        if f.status == AccessibilityStatus.USABLE and f.actionable is True
    }
    effective = frozenset(resident_id for resident_id, _ in timely & usable)
    if len(effective) != count_effective_warning_coverage(delivery, assessment):
        raise AssertionError('Effective residents and existing KPI differ')
    return effective


def run_integrated_recovery(configuration: SimulationConfiguration, *,
                            workbook_path: str | Path | None = None,
                            stage_barrier_resolver: Callable[..., Any] | None = None) -> RecoveryRun:
    """Evaluate P0 then rerun Agents 1/2/3 for at most 3 recovery proposals.

    Crucially, successful technical delivery alone is not evidence that SMS
    segments arrived or audio was played, nor that a person could use the app.
    Missing evidence stays unknown in every plan; no evidence is fabricated.
    """
    baseline = run_integrated_baseline(
        configuration, workbook_path=workbook_path,
        stage_barrier_resolver=stage_barrier_resolver)
    residents = baseline.residents
    original_assignments = baseline.agent1_input.assignments
    original_effective = effective_resident_ids(baseline.delivery, baseline.accessibility)
    baseline_barriers = {
        finding.resident_id for finding in baseline.accessibility.accessibility_findings
        if finding.status == AccessibilityStatus.BARRIER
    }
    by_id = {person.resident_id: person for person in residents}
    evaluated: list[EvaluatedPlan] = []

    def evaluate(candidate: RecoveryCandidate) -> VerifiedEvaluation:
        # The Agent 1 input validates plan IDs, enabled channels and a complete
        # unique assignment roster; all runs reuse the original configuration.
        input1 = Agent1Input(configuration, residents,
                             candidate.assignments, candidate.plan_id)
        delivery = run_agent1(input1)
        delivery.validate_against_input(input1)
        input2 = Agent2Input(configuration, input1, delivery)
        risks = run_agent2(input2)
        risks.validate_against_input(input2, require_complete=True)
        input3 = Agent3Input(
            configuration, input1, delivery, risks,
            FIXTURE_ID, RULES_ID, REGISTRY_ID,
        )
        accessibility = assess_agent3(input3, stage_barrier_resolver=stage_barrier_resolver)
        accessibility.validate_against_input(input3)

        effective = effective_resident_ids(delivery, accessibility)
        metrics = PlanMetrics(
            plan_id=candidate.plan_id,
            estimated_reach_count=count_estimated_reach(delivery),
            effective_coverage_count=len(effective),
            unresolved_critical_count=count_unresolved_critical_cases(risks),
            actual_selected_attempts=delivery.actual_attempt_count,
            resolved_accessibility_gaps=len(baseline_barriers & effective),
        )

        assigned_ids = {
            a.resident_id for a in candidate.assignments
            if a.assignment_status == AssignmentStatus.ASSIGNED
        }
        selected_ids = [r.resident_id for r in delivery.selected_delivery_records]
        technical_prereqs_ok = (
            len(candidate.assignments) == len(residents)
            and len(selected_ids) == len(set(selected_ids))
            and assigned_ids == set(selected_ids)
            and all(
                a.selected_channel in configuration.enabled_channels
                and is_channel_eligible(by_id[a.resident_id], a.selected_channel)
                for a in candidate.assignments
                if a.assignment_status == AssignmentStatus.ASSIGNED
            )
        )

        # Agent 3 reports BOTH authorization and privacy. If either requires
        # review, the candidate is NOT selectable. Do not reinterpret its
        # policy findings as real legal permission.
        findings = {p.check_type: p for p in accessibility.policy_findings}
        auth_finding = findings.get('Authorization')
        privacy_finding = findings.get('Privacy')
        authorization = (auth_finding.status if auth_finding else PolicyCheckStatus.INSUFFICIENT_INFO)
        privacy = (privacy_finding.status if privacy_finding else PolicyCheckStatus.INSUFFICIENT_INFO)
        policy_cleared_for_scenario = (
            authorization == PolicyCheckStatus.NO_ISSUE
            and privacy == PolicyCheckStatus.NO_ISSUE
        )
        # The T+06 EV03 review is explicitly about an EXCLUDED hypothetical
        # external route/data transfer. No recovery candidate contains it.
        # Scope the candidate decision to internal channels without overwriting
        # or hiding the original human-review findings in Agent 3's output.
        outside_channel_review_only = (
            configuration.selected_stage == EventStage.T06
            and authorization == PolicyCheckStatus.REVIEW_REQUIRED
            and privacy == PolicyCheckStatus.REVIEW_REQUIRED
            and auth_finding is not None
            and privacy_finding is not None
            and auth_finding.reason.startswith('EV03 hypothetical outside channel')
            and privacy_finding.reason.startswith('EV03 hypothetical external sharing')
            and all(a.selected_channel is None or a.selected_channel in tuple(ChannelID)
                    for a in candidate.assignments)
        )
        scoped_clear = policy_cleared_for_scenario or outside_channel_review_only
        reviewed_status = (
            PolicyCheckStatus.NO_ISSUE if scoped_clear
            else PolicyCheckStatus.REVIEW_REQUIRED
            if PolicyCheckStatus.REVIEW_REQUIRED in (authorization, privacy)
            else PolicyCheckStatus.INSUFFICIENT_INFO
        )
        scope_note = (
            'EV03 review applies only to excluded hypothetical external route; '
            'review findings remain on Agent 3 and this is not legal approval.'
            if outside_channel_review_only else
            'Scenario-only policy checks; not real-world authorization.'
        )

        barrier_notes = {'blocked': (), 'review_required': ()}
        if stage_barrier_resolver is not None:
            from lastmile_ai.agents.stage_accessibility_adapter import review_recovery_assignments
            barrier_notes = review_recovery_assignments(candidate,
                configuration.selected_stage, stage_barrier_resolver)
            # Unknown remains technically eligible; Agent 3 assesses it as
            # REVIEW and it cannot add confirmed effective coverage.
            technical_prereqs_ok = technical_prereqs_ok and not barrier_notes['blocked']
        evaluated.append(EvaluatedPlan(candidate.plan_id, delivery, risks,
                                      accessibility, metrics, technical_prereqs_ok))
        return VerifiedEvaluation(
            metrics=metrics,
            effective_resident_ids=effective,
            authorization_status=reviewed_status,
            safety_approved=technical_prereqs_ok,
            explanation=(
                f'Real deterministic candidate rerun: technical reach='
                f'{metrics.estimated_reach_count}, confirmed effective='
                f'{metrics.effective_coverage_count}, unresolved technical critical='
                f'{metrics.unresolved_critical_count}; hard prerequisites='
                f'{technical_prereqs_ok}; scenario Authorization={authorization.value}, '
                f'Privacy={privacy.value}; EV02 blocked={len(barrier_notes["blocked"])}, '
                f'EV02 review={len(barrier_notes["review_required"])}. {scope_note}'
            ),
        )

    recovery = run_agent4(
        make_recovery_input(baseline),
        baseline_assignments=original_assignments,
        baseline_effective_ids=original_effective,
        evaluate=evaluate,
        stage_barrier_resolver=stage_barrier_resolver,
    )
    return RecoveryRun(baseline=baseline, recovery=recovery,
                       tested_plans=tuple(evaluated))
