
"""Step 3 metrics: calculate KPIs from actual selected simulation results."""

from lastmile_ai.schemas import Agent1Output, DeliveryStatus

from lastmile_ai.schemas import Agent3Output, AccessibilityStatus, ChannelID

from lastmile_ai.schemas import PlanMetrics, RESIDENT_COUNT

from lastmile_ai.schemas import Agent2Output, RiskPriority


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



