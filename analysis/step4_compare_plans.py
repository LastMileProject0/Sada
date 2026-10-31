"""Step 4 (Salma): audit actual P0-P3 integrated recovery evaluations.

Run from repository root:
    python -m analysis.step4_compare_plans --stage T+00:00
Output is factual Markdown; candidate metrics come from tested_plans even when
Agent 4 correctly excludes a plan from selection.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from lastmile_ai.recovery_runtime import RecoveryRun, run_integrated_recovery
from lastmile_ai.schemas import ChannelID, EventStage, PlanMetrics, SimulationConfiguration


def comparison_rows(run: RecoveryRun) -> list[dict]:
    """Represent all actually evaluated plans, including rejected candidates."""
    candidate_lookup = {candidate.plan_id: candidate for candidate in run.recovery.candidates}
    tested = {plan.plan_id: plan for plan in run.tested_plans}
    if len(tested) != len(run.tested_plans):
        raise ValueError('Duplicate evaluated plan IDs')
    expected = {candidate.plan_id for candidate in run.recovery.candidates}
    if set(tested) != expected:
        raise ValueError('Candidate evaluations and Agent 4 proposals differ')
    plans: list[PlanMetrics] = [run.baseline.metrics]
    plans += [tested[plan_id].metrics for plan_id in sorted(tested)]
    baseline = run.baseline.metrics
    rows = []
    for metrics in plans:
        candidate = candidate_lookup.get(metrics.plan_id)
        rows.append({
            'plan_id': metrics.plan_id,
            'selected': metrics.plan_id == run.recovery.recommended_plan_id,
            'estimated_reach': metrics.estimated_reach_count,
            'effective_coverage': metrics.effective_coverage_count,
            'effective_delta_vs_p0': metrics.effective_coverage_count - baseline.effective_coverage_count,
            'unresolved_critical': metrics.unresolved_critical_count,
            'selected_attempts': metrics.actual_selected_attempts,
            'resolved_accessibility_gaps': metrics.resolved_accessibility_gaps,
            'feasible': True if candidate is None else candidate.feasible,
            'authorization': 'Baseline (scenario)' if candidate is None else candidate.authorization_status.value,
            'decision_reason': 'Standard baseline; no recovery' if candidate is None else candidate.reason,
        })
    return rows


def render_markdown(run: RecoveryRun, config: SimulationConfiguration) -> str:
    rows = comparison_rows(run)
    lines = [
        '# Step 4 — Recovery Evaluation & Decision Audit',
        '',
        f'- Stage: `{config.selected_stage.value}` (cumulative snapshot)',
        f'- Enabled channels: {", ".join(ch.value for ch in config.enabled_channels)}',
        '- Same synthetic residents and scenario conditions across P0–P3.',
        '- Counts are model estimates, **not** observed population behavior or legal clearance.',
        '',
        '| Plan | Selected | Technical reach | Effective coverage | Δ effective vs P0 | Unresolved critical | Attempts | Resolved accessibility gaps | Feasible |',
        '|---|---|---:|---:|---:|---:|---:|---:|---|',
    ]
    for row in rows:
        lines.append('| {plan_id} | {selected} | {estimated_reach} | {effective_coverage} | {effective_delta_vs_p0:+d} | {unresolved_critical} | {selected_attempts} | {resolved_accessibility_gaps} | {feasible} |'.format(
            **{**row, 'selected': 'Yes' if row['selected'] else 'No', 'feasible': 'Yes' if row['feasible'] else 'No'}))
    lines += [
        '', f'## Agent 4 decision: {run.recovery.recommended_plan_id}',
        '', run.recovery.explanation, '',
        f'Effective coverage improvement: **{run.recovery.recovery_improvement_percentage_points:.1f} percentage points** (out of 1,000 simulated residents).',
        '', '## Candidate audit', ''
    ]
    for row in rows[1:]:
        lines.extend([f"### {row['plan_id']}", '',
                      f"- Scenario authorization status: {row['authorization']}",
                      f"- Decision evidence: {row['decision_reason']}", ''])
    if run.recovery.unresolved_review_notes:
        lines.extend(['## Outstanding decision notes', ''])
        lines += [f'- {note}' for note in run.recovery.unresolved_review_notes]
        lines.append('')
    lines += [
        '## Interpretation cautions', '',
        '- Technical reach counts delivered **and delayed** arrivals; effective coverage requires timely, usable, actionable warning evidence.',
        '- A candidate can improve effective coverage while lowering technical reach; do not claim improvement in every KPI.',
        '- Missing usability evidence is **not** proof that a resident failed to understand a warning.',
        '- Digital-signage readability and availability are limited by scenario assumptions, not field validation.',
        '- Authorization/privacy status is scoped to the simulation and must not be presented as real-world legal approval.',
        '',
    ]
    return '\n'.join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', default=EventStage.T00.value,
                        choices=[stage.value for stage in EventStage])
    parser.add_argument('--channels', nargs='+', default=[ch.value for ch in ChannelID],
                        choices=[ch.value for ch in ChannelID])
    parser.add_argument('--output', type=Path, help='Optional Markdown report path')
    args = parser.parse_args(argv)
    config = SimulationConfiguration(EventStage(args.stage), tuple(ChannelID(ch) for ch in args.channels))
    report = render_markdown(run_integrated_recovery(config), config)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding='utf-8')
        print(f'Report saved to: {args.output}')
    else:
        print(report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
