"""Step 3 integration entry point for the approved synthetic P0 baseline.

Connects the real team-owned Agent 1/2/3 implementations to Sirin's existing
pipeline. Does not modify approved dataset, agent code, or warning content.
Recovery (Agent 4) is a separate next integration step.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Any

from lastmile_ai.agents.delivery import run_agent1
from lastmile_ai.agents.policy_accessibility import (
    FIXTURE_ID, REGISTRY_ID, RULES_ID, assess_agent3,
)
from lastmile_ai.agents.risk import run_agent2
from lastmile_ai.agents.scenario_conditions import is_channel_eligible
from lastmile_ai.data.resident_adapter import load_resident_profiles
from lastmile_ai.pipeline import AgentRunners, BaselineResult, run_baseline
from lastmile_ai.schemas import (
    AssignmentStatus, CHANNEL_PRIORITY_P0, PlanAssignment, ResidentProfile,
    SimulationConfiguration,
)


def build_p0_assignments(
    configuration: SimulationConfiguration,
    residents: tuple[ResidentProfile, ...],
) -> tuple[PlanAssignment, ...]:
    """Assign the first eligible, enabled P0 channel; never auto-backup.

    This applies ONLY hard channel prerequisites. Weak coverage, limited
    internet, disability flags, and event-specific failures do not pre-filter
    channels in the Standard Baseline.
    """
    if not isinstance(configuration, SimulationConfiguration):
        raise TypeError('configuration must be SimulationConfiguration')
    if not isinstance(residents, tuple) or any(
        not isinstance(resident, ResidentProfile) for resident in residents
    ):
        raise TypeError('residents must be tuple[ResidentProfile, ...]')

    enabled = set(configuration.enabled_channels)
    assignments = []
    for resident in residents:
        channel = next(
            (ch for ch in CHANNEL_PRIORITY_P0
             if ch in enabled and is_channel_eligible(resident, ch)),
            None,
        )
        assignments.append(PlanAssignment(
            resident_id=resident.resident_id,
            plan_id='P0',
            assignment_status=(
                AssignmentStatus.ASSIGNED
                if channel is not None else AssignmentStatus.NO_ELIGIBLE_CHANNEL
            ),
            selected_channel=channel,
            reason=(f'P0 fixed priority: first enabled eligible {channel.value}'
                    if channel is not None
                    else 'P0: no enabled channel meets hard prerequisites'),
        ))
    return tuple(assignments)


def run_integrated_baseline(
    configuration: SimulationConfiguration,
    *,
    workbook_path: str | Path | None = None,
    stage_barrier_resolver: Callable[..., Any] | None = None,
) -> BaselineResult:
    """Load the approved residents and run actual Agent 1->2->3->metrics.

    Without explicit additional evidence, the accessibility assessment may
    legitimately return Needs Further Review rather than verified coverage.
    """
    if not isinstance(configuration, SimulationConfiguration):
        raise TypeError('configuration must be SimulationConfiguration')
    residents = (load_resident_profiles() if workbook_path is None
                 else load_resident_profiles(workbook_path))
    def stage_aware_agent3(input3):
        return assess_agent3(input3, stage_barrier_resolver=stage_barrier_resolver)

    return run_baseline(
        configuration=configuration,
        residents=residents,
        assignments=build_p0_assignments(configuration, residents),
        runners=AgentRunners(run_agent1, run_agent2,
                             assess_agent3 if stage_barrier_resolver is None else stage_aware_agent3),
        warning_fixture_id=FIXTURE_ID,
        actionability_rules_id=RULES_ID,
        source_registry_id=REGISTRY_ID,
    )
