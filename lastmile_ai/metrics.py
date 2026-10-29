
"""Step 3 metrics: calculate KPIs from actual selected simulation results."""

from lastmile_ai.schemas import Agent1Output, DeliveryStatus

from lastmile_ai.schemas import Agent3Output, AccessibilityStatus, ChannelID

from lastmile_ai.schemas import PlanMetrics, RESIDENT_COUNT

from lastmile_ai.schemas import Agent2Output, RiskPriority

from lastmile_ai.schemas import ResidentProfile


def count_estimated_reach(delivery_results: Agent1Output) -> int:
    """Count unique residents reached by an actually attempted, selected channel.

    Delivered and Delayed both count as technical reach. Unselected potential
    evaluations, failures and unavailable channels never count.
    """
    if not isinstance(delivery_results, Agent1Output):
        raise TypeError("delivery_results must be Agent1Output")

    reached_residents = {
        record.resident_id
        for record in delivery_results.selected_delivery_records
        if record.selected_in_plan
        and record.attempted
        and record.status in (DeliveryStatus.DELIVERED, DeliveryStatus.DELAYED)
    }
    return len(reached_residents)


def count_effective_warning_coverage(
    delivery_results: Agent1Output,
    accessibility_results: Agent3Output,
) -> int:
    """Count unique residents with timely, usable, actionable warnings."""

    if not isinstance(delivery_results, Agent1Output):
        raise TypeError("delivery_results must be Agent1Output")

    if not isinstance(accessibility_results, Agent3Output):
        raise TypeError("accessibility_results must be Agent3Output")

    if delivery_results.plan_id != accessibility_results.plan_id:
        raise ValueError("Results must belong to the same plan")

    timely_arrivals = {
        (record.resident_id, record.channel_id)
        for record in delivery_results.selected_delivery_records
        if record.selected_in_plan
        and record.attempted
        and record.status == DeliveryStatus.DELIVERED
        and record.channel_id != ChannelID.PUBLIC_SIRENS
    }

    usable_actionable = {
        (finding.resident_id, finding.channel_id)
        for finding in accessibility_results.accessibility_findings
        if finding.status == AccessibilityStatus.USABLE
        and finding.actionable is True
    }

    effective_residents = {
        resident_id
        for resident_id, channel_id in timely_arrivals & usable_actionable
    }

    return len(effective_residents)

def calculate_recovery_improvement(
    baseline: PlanMetrics,
    recovery: PlanMetrics,
) -> float:
    """Return improvement in effective coverage, in percentage points."""

    if not isinstance(baseline, PlanMetrics):
        raise TypeError("baseline must be PlanMetrics")

    if not isinstance(recovery, PlanMetrics):
        raise TypeError("recovery must be PlanMetrics")

    if baseline.plan_id != "P0":
        raise ValueError("Baseline plan must be P0")

    if recovery.plan_id not in ("P0", "P1", "P2", "P3"):
        raise ValueError("Invalid recovery plan ID")

    improvement = (
        recovery.effective_coverage_count
        - baseline.effective_coverage_count
    )

    if improvement < 0:
        raise ValueError("Recovery must not reduce effective coverage")

    return (improvement / RESIDENT_COUNT) * 100.0


def count_unresolved_critical_cases(
    risk_results: Agent2Output,
) -> int:
    """Count unique HIGH-risk residents in the evaluated plan.

    Under the approved risk rules, HIGH means no selected warning
    arrived within the 60-second observation window.
    Therefore these residents have no confirmed effective warning.
    """

    if not isinstance(risk_results, Agent2Output):
        raise TypeError("risk_results must be Agent2Output")

    critical_residents = {
        finding.resident_id
        for finding in risk_results.resident_risks
        if finding.priority == RiskPriority.HIGH
    }

    return len(critical_residents)


def count_uncovered_groups(
    residents: tuple[ResidentProfile, ...],
    delivery_results: Agent1Output,
    accessibility_results: Agent3Output,
) -> dict[str, int]:
    """Count residents without confirmed effective coverage by group."""

    if not isinstance(delivery_results, Agent1Output):
        raise TypeError("delivery_results must be Agent1Output")

    if not isinstance(accessibility_results, Agent3Output):
        raise TypeError("accessibility_results must be Agent3Output")

    if delivery_results.plan_id != accessibility_results.plan_id:
        raise ValueError("Results must belong to the same plan")

    if not isinstance(residents, tuple) or any(
        not isinstance(resident, ResidentProfile)
        for resident in residents
    ):
        raise TypeError("residents must be a tuple of ResidentProfile")

    resident_ids = [resident.resident_id for resident in residents]

    if len(resident_ids) != len(set(resident_ids)):
        raise ValueError("Duplicate resident IDs")

    timely_arrivals = {
        (record.resident_id, record.channel_id)
        for record in delivery_results.selected_delivery_records
        if record.selected_in_plan
        and record.attempted
        and record.status == DeliveryStatus.DELIVERED
        and record.channel_id != ChannelID.PUBLIC_SIRENS
    }

    usable_actionable = {
        (finding.resident_id, finding.channel_id)
        for finding in accessibility_results.accessibility_findings
        if finding.status == AccessibilityStatus.USABLE
        and finding.actionable is True
    }

    effective_ids = {
        resident_id
        for resident_id, channel_id in timely_arrivals & usable_actionable
    }

    uncovered = {
        resident.resident_id
        for resident in residents
        if resident.resident_id not in effective_ids
    }

    return {
        "hearing_impairment": sum(
            r.hearing_impairment and r.resident_id in uncovered
            for r in residents
        ),
        "visual_impairment": sum(
            r.visual_impairment and r.resident_id in uncovered
            for r in residents
        ),
        "elderly_65_plus": sum(
            r.elderly_65_plus and r.resident_id in uncovered
            for r in residents
        ),
        "limited_internet": sum(
            r.limited_internet and r.resident_id in uncovered
            for r in residents
        ),
        "weak_mobile_coverage": sum(
            r.weak_mobile_coverage and r.resident_id in uncovered
            for r in residents
        ),
        "unique_uncovered_total": len(uncovered),
    }

def summarize_policy_assessment(
    results: Agent3Output,
) -> dict[str, str]:
    """Describe scenario policy reviews without legal certification."""

    if not isinstance(results, Agent3Output):
        raise TypeError("results must be Agent3Output")

    statuses = {
        "Authorization": "Not Reported",
        "Privacy": "Not Reported",
    }

    for finding in results.policy_findings:
        statuses[finding.check_type] = finding.status.value

    return statuses


def summarize_decision_traceability(
    delivery: Agent1Output,
    risks: Agent2Output,
    assessment: Agent3Output,
) -> dict[str, int]:
    """Summarize documented evidence without inventing sources."""

    if not isinstance(delivery, Agent1Output):
        raise TypeError("delivery must be Agent1Output")

    if not isinstance(risks, Agent2Output):
        raise TypeError("risks must be Agent2Output")

    if not isinstance(assessment, Agent3Output):
        raise TypeError("assessment must be Agent3Output")

    if len({
        delivery.plan_id,
        risks.plan_id,
        assessment.plan_id,
    }) != 1:
        raise ValueError("All results must belong to the same plan")

    evidence_flags = (
        [
            bool(r.evidence.strip())
            for r in delivery.selected_delivery_records
        ]
        + [
            bool(r.evidence)
            for r in risks.resident_risks
        ]
        + [
            bool(f.evidence)
            for f in assessment.accessibility_findings
        ]
        + [
            bool(p.evidence)
            for p in assessment.policy_findings
        ]
    )

    documented = sum(evidence_flags)

    return {
        "findings_total": len(evidence_flags),
        "findings_with_evidence": documented,
        "findings_missing_evidence": len(evidence_flags) - documented,
        "cap_advisory_source_count": (
            len(assessment.cap_advisory.source_ids)
            if assessment.cap_advisory else 0
        ),
    }

