"""Step 3 integration orchestrator (Sereen): no agent algorithms implemented here.

Runs and validates the P0 baseline using injected Agent 1, 2 and 3 functions.
Preparation for Agent 4 is provided via make_recovery_input(). Candidate
simulation/selection will be connected only when the Agent 4 runtime exists.
"""
from dataclasses import dataclass
from typing import Callable

from lastmile_ai.metrics import (
    count_estimated_reach,
    count_effective_warning_coverage,
    count_unresolved_critical_cases,
)
from lastmile_ai.schemas import (
    Agent1Input, Agent1Output, Agent2Input, Agent2Output,
    Agent3Input, Agent3Output, Agent4Input, PlanAssignment,
    PlanMetrics, ResidentProfile, RESIDENT_COUNT, SimulationConfiguration,
    AssignmentStatus,
)


@dataclass(frozen=True)
class AgentRunners:
    """Adapters provided by owners of the runtime modules during integration."""
    agent1: Callable[[Agent1Input], Agent1Output]
    agent2: Callable[[Agent2Input], Agent2Output]
    agent3: Callable[[Agent3Input], Agent3Output]


@dataclass(frozen=True)
class BaselineResult:
    configuration: SimulationConfiguration
    residents: tuple[ResidentProfile, ...]
    agent1_input: Agent1Input
    delivery: Agent1Output
    risks: Agent2Output
    accessibility: Agent3Output
    metrics: PlanMetrics


def run_baseline(
    configuration: SimulationConfiguration,
    residents: tuple[ResidentProfile, ...],
    assignments: tuple[PlanAssignment, ...],
    runners: AgentRunners,
    *,
    warning_fixture_id: str,
    actionability_rules_id: str,
    source_registry_id: str,
) -> BaselineResult:
    """Run validated P0: Agent 1 -> Agent 2 -> Agent 3 -> KPI summary.

    The planner only controls configuration. Residents and P0 assignments
    must come from approved fixed data / another team-owned runtime.
    """
    if not isinstance(runners, AgentRunners):
        raise TypeError('runners must be AgentRunners')
    if not isinstance(residents, tuple) or len(residents) != RESIDENT_COUNT:
        raise ValueError(f'Expected the fixed {RESIDENT_COUNT}-resident roster')

    input1 = Agent1Input(configuration, residents, assignments, plan_id='P0')
    delivery = runners.agent1(input1)
    if not isinstance(delivery, Agent1Output):
        raise TypeError('Agent 1 must return Agent1Output')
    delivery.validate_against_input(input1)

    # P0 must have exactly one selected result for each assigned resident.
    assigned_ids = {a.resident_id for a in assignments
                    if a.assignment_status == AssignmentStatus.ASSIGNED}
    selected_ids = [r.resident_id for r in delivery.selected_delivery_records]
    if set(selected_ids) != assigned_ids or len(selected_ids) != len(assigned_ids):
        raise ValueError('P0 requires exactly one selected result per assigned resident')

    input2 = Agent2Input(configuration, input1, delivery)
    risks = runners.agent2(input2)
    if not isinstance(risks, Agent2Output):
        raise TypeError('Agent 2 must return Agent2Output')
    risks.validate_against_input(input2, require_complete=True)

    input3 = Agent3Input(
        configuration, input1, delivery, risks,
        warning_fixture_id, actionability_rules_id, source_registry_id,
    )
    accessibility = runners.agent3(input3)
    if not isinstance(accessibility, Agent3Output):
        raise TypeError('Agent 3 must return Agent3Output')
    accessibility.validate_against_input(input3)

    metrics = PlanMetrics(
        plan_id='P0',
        estimated_reach_count=count_estimated_reach(delivery),
        effective_coverage_count=count_effective_warning_coverage(delivery, accessibility),
        unresolved_critical_count=count_unresolved_critical_cases(risks),
        actual_selected_attempts=delivery.actual_attempt_count,
        resolved_accessibility_gaps=0,  # P0 has no recovery comparison.
    )
    return BaselineResult(configuration, residents, input1, delivery,
                          risks, accessibility, metrics)


def make_recovery_input(result: BaselineResult) -> Agent4Input:
    """Create the approved Agent 4 handoff; do not fabricate candidate runs."""
    if not isinstance(result, BaselineResult):
        raise TypeError('result must be BaselineResult')
    return Agent4Input(
        configuration=result.configuration,
        baseline_metrics=result.metrics,
        baseline_risks=result.risks,
        baseline_assessment=result.accessibility,
        residents=result.residents,
    )
