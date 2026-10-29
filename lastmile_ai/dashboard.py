"""LastMile AI simulation dashboard, using traceable Step 3 agent outputs.

Backward compatible: build_dashboard(Agent4Output) renders the four headline KPIs.
For detailed FR-06 views pass the complete RecoveryRun from run_integrated_recovery().
There are no real warnings, live data, or inferred per-person accessibility facts.
"""
from collections import Counter
from html import escape

from lastmile_ai.schemas import (
    AccessibilityStatus, Agent4Output, ChannelID, DeliveryStatus, RESIDENT_COUNT,
)
from lastmile_ai.recovery_runtime import RecoveryRun, effective_resident_ids

_CHANNELS = (
    (ChannelID.SMS, 'SMS'),
    (ChannelID.MOBILE_APP, 'Mobile App'),
    (ChannelID.VOICE_CALL, 'Voice Call'),
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


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _headline(result: Agent4Output) -> str:
    before, after = result.baseline_metrics, result.final_metrics
    improvement = (after.effective_coverage_count - before.effective_coverage_count) / RESIDENT_COUNT * 100
    cards = (
        ('Estimated Reach', f'{after.estimated_reach_count:,} / {RESIDENT_COUNT:,}'),
        ('Effective Warning Coverage', f'{after.effective_coverage_count:,} / {RESIDENT_COUNT:,}'),
        ('Recovery Improvement', f'{improvement:.1f} percentage points'),
        ('Unresolved Critical Cases', f'{after.unresolved_critical_count:,}'),
    )
    return '\n'.join(
        f'<section class="card"><h2>{_e(title)}</h2><p class="big">{_e(value)}</p></section>'
        for title, value in cards
    )


def _overview(result: Agent4Output) -> str:
    before, after = result.baseline_metrics, result.final_metrics
    return (
        '<section class="card"><h2>Before vs After — baseline and selected plan</h2>'
        '<table><thead><tr><th>Metric</th><th>P0 baseline</th><th>Final plan</th></tr></thead><tbody>'
        f'<tr><th>Estimated Reach</th><td>{before.estimated_reach_count}</td><td>{after.estimated_reach_count}</td></tr>'
        f'<tr><th>Effective Warning Coverage</th><td>{before.effective_coverage_count}</td><td>{after.effective_coverage_count}</td></tr>'
        f'<tr><th>Unresolved Critical Cases</th><td>{before.unresolved_critical_count}</td><td>{after.unresolved_critical_count}</td></tr>'
        '</tbody></table></section>'
    )


def _group_counts(residents: tuple, plan) -> dict[str, tuple[int, int, int]]:
    """One category per resident per group: confirmed-effective, needs-review, or gap.

    Gap covers unavailable/failed/delayed/nonactionable/known barriers; review is
    deliberately separate. A person may belong to several demographic groups.
    """
    effective = effective_resident_ids(plan.delivery, plan.accessibility)
    reviews = {f.resident_id for f in plan.accessibility.accessibility_findings
               if f.status == AccessibilityStatus.REVIEW}
    result = {}
    for label, flag in _GROUPS:
        members = {r.resident_id for r in residents if getattr(r, flag)}
        effective_n = len(members & effective)
        review_n = len((members - effective) & reviews)
        result[label] = (len(members), len(members) - effective_n - review_n, review_n)
    return result


def _group_section(run: RecoveryRun, final_plan) -> str:
    before = _group_counts(run.baseline.residents, run.baseline)
    after = _group_counts(run.baseline.residents, final_plan)
    rows = []
    for label, _ in _GROUPS:
        population, gap0, review0 = before[label]
        _, gap1, review1 = after[label]
        rows.append(
            f'<tr><th>{_e(label)}</th><td>{population}</td><td>{gap0}</td>'
            f'<td>{gap1}</td><td>{review0}</td><td>{review1}</td></tr>'
        )
    return (
        '<section class="card"><h2>1. Accessibility &amp; Affected Groups</h2>'
        '<p>Gaps exclude needs-review cases; one category per resident within each group. '
        'Groups can overlap, so do not sum rows.</p>'
        '<table><thead><tr><th>Group</th><th>Population</th><th>Before gaps</th>'
        '<th>After gaps</th><th>Before review</th><th>After review</th></tr></thead><tbody>'
        + ''.join(rows) + '</tbody></table></section>'
    )


def _channel_table(plan, enabled: set) -> str:
    records = plan.delivery.selected_delivery_records
    rows = []
    for channel, label in _CHANNELS:
        selected = [r for r in records if r.channel_id == channel and r.selected_in_plan]
        counts = Counter(r.status for r in selected)
        attempts = sum(bool(r.attempted) for r in selected)
        rows.append(
            f'<tr><th>{_e(channel.value)} — {_e(label)}</th>'
            f'<td>{"Yes" if channel in enabled else "No"}</td><td>{attempts}</td>'
            + ''.join(f'<td>{counts[status]}</td>' for status in DeliveryStatus)
            + '</tr>'
        )
    return (
        '<table><thead><tr><th>Channel</th><th>Enabled</th><th>Selected attempts</th>'
        '<th>Delivered</th><th>Delayed</th><th>Failed</th><th>Unavailable</th>'
        '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table>'
        f'<p class="small">No Eligible Channel assignments (not attempts): '
        f'{len(plan.delivery.no_eligible_assignments)}</p>'
    )


def _channels_section(run: RecoveryRun, final_plan) -> str:
    enabled = set(run.baseline.configuration.enabled_channels)
    return (
        '<section class="card"><h2>2. Channel Performance</h2>'
        '<p>Counts use selected records only; potential-channel evaluations are excluded.</p>'
        '<div class="tabs"><input checked type="radio" name="channel_view" id="view_before">'
        '<label for="view_before">Before · P0</label>'
        '<input type="radio" name="channel_view" id="view_after">'
        f'<label for="view_after">After · {_e(run.recovery.recommended_plan_id)}</label>'
        '<div class="before_view">' + _channel_table(run.baseline, enabled) + '</div>'
        '<div class="after_view">' + _channel_table(final_plan, enabled) + '</div></div></section>'
    )


def _plan_section(run: RecoveryRun) -> str:
    items = {plan.plan_id: plan for plan in run.tested_plans}
    candidates = {candidate.plan_id: candidate for candidate in run.recovery.candidates}
    rows = []
    for plan_id in ('P0', 'P1', 'P2', 'P3'):
        if plan_id == 'P0':
            m = run.baseline.metrics
            status, reason = 'Baseline', 'Fixed deterministic channel priority; no recovery'
        elif plan_id in items:
            m = items[plan_id].metrics
            cand = candidates.get(plan_id)
            status = 'Feasible' if cand and cand.feasible else 'Not selected / review'
            reason = cand.reason if cand else 'Verified simulation executed; decision unavailable'
        else:
            m = None
            status, reason = 'Not tested', 'No candidate evaluated'
        if m is not None:
            cells = (m.estimated_reach_count, m.effective_coverage_count,
                     m.unresolved_critical_count)
            data = ''.join(f'<td>{number}</td>' for number in cells)
        else:
            data = '<td>—</td>' * 3
        chosen = ' <strong>(Recommended)</strong>' if plan_id == run.recovery.recommended_plan_id else ''
        rows.append(f'<tr><th>{_e(plan_id)}{chosen}</th>{data}<td>{_e(status)}</td>'
                    f'<td class="wrap">{_e(reason)}</td></tr>')
    return (
        '<section class="card"><h2>3. AI Recommendation &amp; Tested Recovery Plans</h2>'
        '<table><thead><tr><th>Plan</th><th>Estimated reach</th><th>Effective coverage</th>'
        '<th>Unresolved critical</th><th>Decision</th><th>Reason</th></tr></thead><tbody>'
        + ''.join(rows) + '</tbody></table></section>'
    )


def _findings_section(final_plan) -> str:
    assessment = final_plan.accessibility
    status_counts = Counter(f.status for f in assessment.accessibility_findings)
    rows = ''.join(
        f'<tr><th>{_e(status.value)}</th><td>{status_counts[status]}</td></tr>'
        for status in AccessibilityStatus
    )
    policy_rows = ''.join(
        '<tr><th>' + _e(p.check_type) + '</th><td>' + _e(p.status.value)
        + '</td><td class="wrap">' + _e(p.reason) + '</td><td>'
        + _e(', '.join(ref.reference_id for ref in p.evidence)) + '</td></tr>'
        for p in assessment.policy_findings
    )
    advisory = assessment.cap_advisory
    cap = (f'<p>CAP advisory only: {_e(advisory.note)}; sources: '
           f'{_e(", ".join(advisory.source_ids))}</p>') if advisory else ''
    return (
        '<section class="card"><h2>4. Accessibility &amp; Policy Review</h2>'
        '<h3>Accessibility assessments — selected plan</h3>'
        '<table><thead><tr><th>Status</th><th>Residents</th></tr></thead><tbody>'
        + rows + '</tbody></table>'
        '<h3>Scenario policy findings (not legal certification)</h3>'
        '<table><thead><tr><th>Check</th><th>Status</th><th>Reason</th><th>Source IDs</th>'
        '</tr></thead><tbody>' + policy_rows + '</tbody></table>' + cap + '</section>'
    )


def build_dashboard(result: Agent4Output | RecoveryRun) -> str:
    """Build standalone HTML from Agent 4 summary or full real RecoveryRun.

    With a summary only, detailed sections are explicitly marked unavailable;
    no per-resident information is invented. The original API remains valid.
    """
    details = result if isinstance(result, RecoveryRun) else None
    summary = result.recovery if details is not None else result
    if not isinstance(summary, Agent4Output):
        raise TypeError('result must be Agent4Output or RecoveryRun')

    sections = ''
    if details is not None:
        selected = (details.baseline if summary.recommended_plan_id == 'P0' else
                    next((p for p in details.tested_plans
                          if p.plan_id == summary.recommended_plan_id), None))
        if selected is None:
            raise ValueError('Recommended plan has no evaluated simulation records')
        sections = (_group_section(details, selected) + _channels_section(details, selected)
                    + _plan_section(details) + _findings_section(selected))
        ctx = ('<p class="context">Stage: ' + _e(details.baseline.configuration.selected_stage.value)
               + ' · Enabled: ' + _e(', '.join(c.value for c in details.baseline.configuration.enabled_channels))
               + ' · Synthetic residents: ' + str(RESIDENT_COUNT) + '</p>')
    else:
        ctx = '<p class="context">Detailed resident/channel data not supplied; summary only.</p>'
        sections = '<section class="card"><p>Detailed accessibility and channel views require RecoveryRun.</p></section>'
    notes = ''.join(f'<li>{_e(note)}</li>' for note in summary.unresolved_review_notes)
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LastMile AI — Simulation Dashboard</title>
<style>
*{box-sizing:border-box}body{font-family:Arial,sans-serif;background:#f5f7fb;color:#18253a;margin:0 auto;max-width:1300px;padding:24px;line-height:1.55}
h1{margin-bottom:0}h2{font-size:1.08rem;margin-top:0}.context,.small,.note{color:#475569}.small{font-size:.87rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:22px 0}.card{background:white;border:1px solid #e3e8f0;border-radius:12px;padding:20px;margin:16px 0;box-shadow:0 1px 5px #10203008}
.big{font-size:1.65rem;font-weight:700;margin:.3em 0}table{border-collapse:collapse;width:100%;margin:14px 0;font-size:.9rem}
th,td{border-bottom:1px solid #dfe5ee;padding:9px;text-align:left;vertical-align:top}thead{background:#f0f4fb}th{font-weight:600}.wrap{max-width:390px;overflow-wrap:anywhere}strong{color:#154da1}
.tabs input{position:absolute;opacity:0}.tabs label{display:inline-block;padding:9px 15px;cursor:pointer;border:1px solid #cdd5e1;border-radius:8px;margin:0 7px 8px 0}.before_view,.after_view{display:none;overflow-x:auto}
#view_before:checked~.before_view,#view_after:checked~.after_view{display:block}
#view_before:checked+label,#view_after:checked+label{background:#183d7a;color:white}
.tabs input:focus-visible+label{outline:3px solid #77aaff}section.card{overflow-x:auto}
@media(max-width:650px){body{padding:12px}th,td{padding:6px;font-size:.78rem}}
</style></head><body>''' + (
        '<h1>LastMile AI — Simulation Dashboard</h1>'
        '<p class="note">Pre-event synthetic planning only. No real alerts sent; no CAP or legal compliance certification.</p>'
        + ctx + '<div class="grid">' + _headline(summary) + '</div>'
        + _overview(summary) + sections
        + '<section class="card"><h2>5. Final Recommendation &amp; Explanation</h2>'
        f'<p><strong>Outcome:</strong> {_e(summary.outcome.value)} · '
        f'<strong>Plan:</strong> {_e(summary.recommended_plan_id)}</p>'
        f'<p>{_e(summary.explanation)}</p>'
        + ('<h3>Unresolved review notes</h3><ul>' + notes + '</ul>' if notes else '')
        + '<p class="small">Estimated reach includes Delivered and Delayed (up to 60 seconds). '
        'Effective warning coverage requires an on-time, usable, actionable selected channel; '
        'sirens alone never count. Group gaps and review categories are modeled, not observed.</p>'
        '</section></body></html>'
    )
