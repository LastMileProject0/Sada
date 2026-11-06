"""LastMile AI Step 3: auditable Markdown report (FR-06).

Call build_report(RecoveryRun) for the complete synthetic simulation report;
legacy build_report(Agent4Output) still works but transparently marks any
unavailable resident/channel detail. No live warning or legal/CAP certification.
"""
from collections import Counter

from lastmile_ai.schemas import (
    AccessibilityStatus, Agent4Output, ChannelID, DeliveryStatus,
    RecoveryOutcome, RESIDENT_COUNT, SCENARIO_ID,
)
from lastmile_ai.recovery_runtime import RecoveryRun, effective_resident_ids

_CHANNELS = (
    (ChannelID.SMS, 'SMS'),
    (ChannelID.MOBILE_APP, 'Mobile App'),
    (ChannelID.VOICE_CALL, 'Automated Voice Call'),
    (ChannelID.PUBLIC_SIRENS, 'Public Sirens'),
    (ChannelID.DIGITAL_SIGNAGE, 'Digital Signage'),
)
_GROUPS = (
    ('Age 65+', 'elderly_65_plus'),
    ('Hearing impairment', 'hearing_impairment'),
    ('Visual impairment', 'visual_impairment'),
    ('Limited internet', 'limited_internet'),
    ('Weak mobile coverage', 'weak_mobile_coverage'),
)


def _cell(value: object) -> str:
    """Keep Markdown tables intact even with user-facing agent reasons."""
    return str(value).replace('\\', '\\\\').replace('|', '\\|').replace('\r', ' ').replace('\n', ' ').strip()


def _refs(evidence, *, aggregate_resident_evidence: bool = False) -> str:
    identifiers = {ref.reference_id for ref in evidence}
    if aggregate_resident_evidence:
        # Exact DELIVERY-Rxxxx IDs remain available in each Agent 3 record.
        # Grouping by those one-per-person IDs would make the printed report
        # 1,000+ rows long without adding useful aggregate insight.
        identifiers = {item for item in identifiers if not item.startswith('DELIVERY-R')}
    return ', '.join(sorted(identifiers)) or 'Individual delivery records only'


def _plan_for(run: RecoveryRun, plan_id: str):
    if plan_id == 'P0':
        return run.baseline
    return next((p for p in run.tested_plans if p.plan_id == plan_id), None)


def _groups(residents, plan):
    effective = effective_resident_ids(plan.delivery, plan.accessibility)
    review = {finding.resident_id
              for finding in plan.accessibility.accessibility_findings
              if finding.status == AccessibilityStatus.REVIEW}
    rows = {}
    for label, attr in _GROUPS:
        members = {person.resident_id for person in residents if getattr(person, attr)}
        confirmed = len(members & effective)
        need_review = len((members - effective) & review)
        rows[label] = (len(members), len(members) - confirmed - need_review, need_review)
    return rows


def _channel_rows(plan, enabled):
    rows = []
    for channel, label in _CHANNELS:
        selected = [r for r in plan.delivery.selected_delivery_records
                    if r.selected_in_plan and r.channel_id == channel]
        counts = Counter(record.status for record in selected)
        columns = [channel.value + ' ' + label, 'Yes' if channel in enabled else 'No',
                   str(sum(r.attempted for r in selected))]
        columns.extend(str(counts[status]) for status in (
            DeliveryStatus.DELIVERED, DeliveryStatus.DELAYED,
            DeliveryStatus.FAILED, DeliveryStatus.UNAVAILABLE,
        ))
        rows.append('| ' + ' | '.join(_cell(column) for column in columns) + ' |')
    return rows


def _add_group_tables(lines, run, final):
    residents = run.baseline.residents
    before = _groups(residents, run.baseline)
    after = _groups(residents, final)
    lines.extend([
        '### Affected groups and accessibility gaps',
        '',
        'Each resident belongs to exactly one of **confirmed effective**, **gap**, or '
        '**needs review** within a group. Groups overlap; do not sum group rows.',
        '',
        '| Group | Population | Before gaps | After gaps | Before review | After review |',
        '|---|---:|---:|---:|---:|---:|',
    ])
    for label, _ in _GROUPS:
        total, b_gap, b_review = before[label]
        _, a_gap, a_review = after[label]
        lines.append(f'| {label} | {total} | {b_gap} | {a_gap} | {b_review} | {a_review} |')
    lines.append('')


def _add_channel_tables(lines, run, final):
    enabled = set(run.baseline.configuration.enabled_channels)
    lines.extend([
        '### Selected-channel performance',
        '',
        'Only **selected** Agent 1 records count. Potential evaluations are excluded. '
        'Delivered: arrival within 30s; Delayed: >30s through 60s; Failed and '
        'Unavailable are separate. Selected attempts exclude Unavailable.',
    ])
    for title, plan in [('Before — P0', run.baseline),
                        (f'After — {run.recovery.recommended_plan_id}', final)]:
        lines.extend([
            '', f'**{title}**', '',
            '| Channel | Enabled | Selected attempts | Delivered | Delayed | Failed | Unavailable |',
            '|---|---|---:|---:|---:|---:|---:|',
        ])
        lines.extend(_channel_rows(plan, enabled))
        lines.extend(['', 'No Eligible Channel assignments (no attempt): '
                      f'{len(plan.delivery.no_eligible_assignments)}.', ''])


def _add_accessibility_findings(lines, plan):
    lines.extend([
        '### Accessibility assessment — final selected plan', '',
        '| Status | Resident findings |', '|---|---:|',
    ])
    counts = Counter(item.status for item in plan.accessibility.accessibility_findings)
    for status in AccessibilityStatus:
        lines.append(f'| {_cell(status.value)} | {counts[status]} |')
    lines.extend([
        '', '#### Traceable accessibility reasons (aggregated)', '',
        'Individual delivery evidence references remain in the Agent 3 records; '
        'this table summarizes by shared fixture/channel references.', '',
        '| Assessment | Reason | Shared evidence source IDs | Findings |',
        '|---|---|---|---:|',
    ])
    groups = Counter((item.status.value, item.reason,
                      _refs(item.evidence, aggregate_resident_evidence=True))
                     for item in plan.accessibility.accessibility_findings)
    for (status, reason, refs), count in sorted(groups.items()):
        lines.append(f'| {_cell(status)} | {_cell(reason)} | {_cell(refs)} | {count} |')
    if not groups:
        lines.append('| Not available | No accessibility findings supplied | — | 0 |')
    lines.append('')


def _add_policy_findings(lines, run, final):
    lines.extend([
        '### Scenario-only Policy assessment', '',
        'These findings are **not legal authorization or a compliance certificate**. '
        'Authorization and Privacy are independent checks. Source IDs refer to '
        'the supplied source registry; CAP comments are explanatory only.', '',
        '| Plan | Check | Assessment | Reason | Evidence source IDs |',
        '|---|---|---|---|---|',
    ])
    for label, plan in [('P0 baseline', run.baseline),
                        (f'{run.recovery.recommended_plan_id} final', final)]:
        policy_findings = plan.accessibility.policy_findings
        if not policy_findings:
            lines.append(f'| {_cell(label)} | Not available | Not assessed | No policy findings supplied | — |')
        for finding in policy_findings:
            lines.append('| ' + ' | '.join(map(_cell, (
                label, finding.check_type, finding.status.value,
                finding.reason, _refs(finding.evidence)
            ))) + ' |')
    advisory = final.accessibility.cap_advisory
    if advisory:
        lines.extend(['', f'CAP advisory (explanation only): {_cell(advisory.note)}',
                      'CAP source IDs: ' + ', '.join(advisory.source_ids) + '.'])
    lines.append('')


def build_report(result: Agent4Output | RecoveryRun) -> str:
    """Return a five-section Markdown report from actual Agent results, if supplied.

    Summary-only API is kept for existing Step 3 consumers/tests. Details that
    require actual per-resident records are never guessed from the KPI counts.
    """
    run = result if isinstance(result, RecoveryRun) else None
    summary = run.recovery if run is not None else result
    if not isinstance(summary, Agent4Output):
        raise TypeError('result must be Agent4Output or RecoveryRun')

    before, after = summary.baseline_metrics, summary.final_metrics
    improvement = summary.recovery_improvement_percentage_points
    lines = [
        '# LastMile AI — Simulation Report', '',
        '**Synthetic pre-event planning only.** No emergency alert was sent. '
        'No CAP pass/fail or legal compliance certification is provided.', '',
        '## 1. Simulation Overview', '',
    ]
    if run is not None:
        config = run.baseline.configuration
        zones = Counter(person.zone for person in run.baseline.residents)
        lines.extend([
            f'- Fixed scenario: `{SCENARIO_ID}` (synthetic flood warning).',
            f'- Population: {len(run.baseline.residents):,} synthetic residents.',
            '- Zones: ' + ', '.join(f'{zone}: {zones[zone]}' for zone in ('Zone A', 'Zone B', 'Zone C')) + '.',
            f'- Selected cumulative snapshot: `{config.selected_stage.value}`; fresh evaluation.',
            '- Planner-enabled channels: ' + ', '.join(channel.value for channel in config.enabled_channels) + '.',
            '- Delivery interpretation: 0–30 seconds Delivered; 31–60 seconds Delayed; '
            'otherwise Failed, or Unavailable if hard prerequisites are absent.',
            '- Comparison: deterministic P0 versus proposed recovery plans '
            'under identical residents, stage, enabled channels and fixed warning.',
        ])
    else:
        lines.extend([
            '- Resident-level configuration, selected stage, enabled channels and '
            'zone breakdown: **Not supplied** (Agent 4 summary only).',
            '- Fixed simulation population used for KPI percentage points: '
            f'{RESIDENT_COUNT:,}.',
        ])

    lines.extend([
        '', '## 2. Before vs After Results', '',
        '| Metric | Baseline P0 | Final plan |', '|---|---:|---:|',
        f'| Estimated Reach | {before.estimated_reach_count} | {after.estimated_reach_count} |',
        f'| Effective Warning Coverage | {before.effective_coverage_count} | {after.effective_coverage_count} |',
        f'| Unresolved Critical Cases | {before.unresolved_critical_count} | {after.unresolved_critical_count} |',
        '', f'**Recovery improvement: {improvement:.1f} percentage points.**',
        '', 'Estimated Reach includes Delivered and Delayed; Effective Warning Coverage '
        'counts only confirmed timely, usable, actionable selected channels. '
        'Sirens are alert-only and never sufficient on their own.', '',
        '## 3. Tested Recovery Plans', '',
        '| Plan | Estimated Reach | Effective Coverage | Unresolved Critical | Decision / reason |',
        '|---|---:|---:|---:|---|',
    ])
    lines.append(f'| P0 (baseline) | {before.estimated_reach_count} | '
                 f'{before.effective_coverage_count} | {before.unresolved_critical_count} | '
                 'Fixed priority, no accessibility-aware recovery |')
    candidates = {candidate.plan_id: candidate for candidate in summary.candidates}
    evaluated = ({plan.plan_id: plan for plan in run.tested_plans} if run is not None else {})
    for plan_id in ('P1', 'P2', 'P3'):
        candidate = candidates.get(plan_id)
        if candidate is None:
            lines.append(f'| {plan_id} | — | — | — | Not proposed |')
            continue
        verified = evaluated.get(plan_id)
        metrics = verified.metrics if verified is not None else candidate.tested_metrics
        if metrics is None:
            vals = ('—', '—', '—')
        else:
            vals = (str(metrics.estimated_reach_count),
                    str(metrics.effective_coverage_count),
                    str(metrics.unresolved_critical_count))
        status = 'Feasible' if candidate.feasible else 'Not feasible'
        selected = ' **Selected**' if plan_id == summary.recommended_plan_id else ''
        reason = _cell(f'{status}{selected}; scenario authorization: '
                       f'{candidate.authorization_status.value}; {candidate.reason}')
        lines.append(f'| {plan_id} | {vals[0]} | {vals[1]} | {vals[2]} | {reason} |')
    if run is None:
        lines.extend(['', 'Detailed tested-run records were not supplied; '
                      'only Agent 4 candidate summary evidence is displayed.'])
    lines.extend(['', '## 4. Accessibility & Policy Findings', ''])
    if run is None:
        lines.extend([
            'Detailed before/after accessibility group gaps and review statuses: '
            '**Not supplied** (requires real Agent 1 and Agent 3 resident records).', '',
            'Per-channel selected attempts and delivery outcomes: **Not supplied**.', '',
            'Authorization/Privacy findings and source-specific reasons: '
            '**Not supplied** (requires Agent 3 output).', '',
        ])
    else:
        final = _plan_for(run, summary.recommended_plan_id)
        if final is None:
            raise ValueError('Recommended plan has no evaluated simulation records')
        _add_group_tables(lines, run, final)
        _add_channel_tables(lines, run, final)
        _add_accessibility_findings(lines, final)
        _add_policy_findings(lines, run, final)

    lines.extend([
        '## 5. Final Recommendation & Explanation', '',
        f'- Outcome: **{_cell(summary.outcome.value)}**.',
        f'- Recommended plan: **{_cell(summary.recommended_plan_id)}**.',
        f'- Final confirmed effective coverage: {after.effective_coverage_count} '
        f'of {RESIDENT_COUNT} synthetic residents.',
        f'- Unresolved critical technical cases: {after.unresolved_critical_count}.',
        f'- Decision explanation: {_cell(summary.explanation)}',
    ])
    if summary.outcome == RecoveryOutcome.NO_SUITABLE_PLAN:
        lines.append('- No suitable recovery found: retain P0; do **not** claim any recovery improvement.')
    if summary.unresolved_review_notes:
        lines.extend(['', '### Unresolved reviews', ''])
        lines.extend('- ' + _cell(note) for note in summary.unresolved_review_notes)
    lines.extend(['', 'All numeric outcomes reflect the controlled synthetic scenario, '
                  'not measured public-alert performance.', ''])
    return '\n'.join(lines)
