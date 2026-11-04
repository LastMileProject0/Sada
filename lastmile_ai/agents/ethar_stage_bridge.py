"""Verified, opt-in bridge from Ethar's EV02 assessment into Agents 3 and 4.

Ethar owns accessibility_stage.py unchanged. This bridge only translates her
status vocabulary into the existing Salma stage_barrier_resolver contract.
It does not infer permanent provenance or assign technical delivery channels.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from lastmile_ai.accessibility_stage import BarrierStatus, assess_accessibility_barrier
from lastmile_ai.data.resident_adapter import load_resident_profiles
from lastmile_ai.schemas import ChannelID, EventStage, ResidentProfile, SimulationConfiguration


_TRANSLATE = {
    BarrierStatus.ACTIVE_EV02: ("Barrier", "EV02"),
    BarrierStatus.ACTIVE_PERMANENT: ("Barrier", "Permanent"),
    BarrierStatus.UNKNOWN: ("Unknown", "Undetermined"),
    BarrierStatus.NO_RECORDED_BARRIER: ("NoKnownBarrier", "None"),
}


def make_ethar_stage_resolver(residents: Iterable[ResidentProfile]):
    """Adapt Ethar's read-only resident assessments to ev02_barrier.v1."""
    by_id = {person.resident_id: person for person in residents}
    if len(by_id) == 0:
        raise ValueError("Resolver requires actual resident profiles")

    def resolve(resident_id: str, stage: EventStage, channel: ChannelID) -> dict:
        """Return a traceable status for one known resident and channel."""
        if resident_id not in by_id:
            raise ValueError(f"Unknown resident ID: {resident_id}")
        if channel not in (ChannelID.VOICE_CALL, ChannelID.DIGITAL_SIGNAGE):
            raise ValueError("EV02 scope only supports CH03 and CH05")
        assessment = assess_accessibility_barrier(by_id[resident_id], channel, stage)
        if assessment.status not in _TRANSLATE:
            raise ValueError(f"Unsupported Ethar status: {assessment.status}")
        status, origin = _TRANSLATE[assessment.status]
        # Only verified event source metadata is cited for confirmed EV02.
        # Unknown provenance remains unknown: no fabricated permanent evidence.
        refs = (["MASTER-PROFILE-RULES:BL-01", "EVENT:EV02"]
                if assessment.status is BarrierStatus.ACTIVE_EV02 else [])
        if assessment.status is BarrierStatus.ACTIVE_PERMANENT:
            raise ValueError("Permanent barrier requires separately approved provenance")
        return {
            "schema_version": "ev02_barrier.v1",
            "resident_id": assessment.resident_id,
            "stage": assessment.stage.value,
            "channel_id": assessment.channel_id.value,
            "barrier_status": status,
            "barrier_origin": origin,
            "reason": assessment.evidence,
            "evidence_refs": refs,
        }

    return resolve


def run_ethar_integrated_baseline(configuration: SimulationConfiguration, *,
                                  workbook_path: str | Path | None = None):
    """Run actual P0 plus stage-aware Agent 3; keep delivery unchanged."""
    from lastmile_ai.runtime import run_integrated_baseline
    residents = load_resident_profiles(workbook_path) if workbook_path is not None else load_resident_profiles()
    return run_integrated_baseline(configuration, workbook_path=workbook_path,
                                   stage_barrier_resolver=make_ethar_stage_resolver(residents))


def run_ethar_integrated_recovery(configuration: SimulationConfiguration, *,
                                  workbook_path: str | Path | None = None):
    """Rerun real P0/P1/P2/P3 with Ethar's source-based EV02 semantics."""
    from lastmile_ai.recovery_runtime import run_integrated_recovery
    residents = load_resident_profiles(workbook_path) if workbook_path is not None else load_resident_profiles()
    return run_integrated_recovery(configuration, workbook_path=workbook_path,
                                   stage_barrier_resolver=make_ethar_stage_resolver(residents))


def compare_stages():
    """Produce before/after audited metrics for all requested test scenarios."""
    from lastmile_ai.recovery_runtime import run_integrated_recovery
    scenarios = [(stage, tuple(ChannelID), stage.value) for stage in EventStage]
    scenarios.append((EventStage.T02,
                      tuple(ch for ch in ChannelID if ch is not ChannelID.SMS),
                      "T+02:00 / CH01 disabled"))
    rows = []
    residents = load_resident_profiles()
    resolver = make_ethar_stage_resolver(residents)
    for stage, enabled, label in scenarios:
        configuration = SimulationConfiguration(stage, enabled)
        before = run_integrated_recovery(configuration)
        after = run_integrated_recovery(configuration, stage_barrier_resolver=resolver)
        def summarize(run):
            return {
                "P0_estimated_reach": run.baseline.metrics.estimated_reach_count,
                "P0_effective_coverage": run.baseline.metrics.effective_coverage_count,
                "P0_unresolved_critical": run.baseline.metrics.unresolved_critical_count,
                "selected_plan": run.recovery.recommended_plan_id,
                "final_estimated_reach": run.recovery.final_metrics.estimated_reach_count,
                "final_effective_coverage": run.recovery.final_metrics.effective_coverage_count,
                "final_unresolved_critical": run.recovery.final_metrics.unresolved_critical_count,
            }
        if before.baseline.delivery != after.baseline.delivery:
            raise AssertionError("EV02 integration changed P0 delivery simulation")
        rows.append({"scenario": label, "without_ethar": summarize(before),
                     "with_ethar": summarize(after),
                     "selected_plan_changed": before.recovery.recommended_plan_id != after.recovery.recommended_plan_id})
    return rows


if __name__ == "__main__":
    print(json.dumps(compare_stages(), indent=2, ensure_ascii=False))
