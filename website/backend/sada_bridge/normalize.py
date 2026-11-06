"""Map *actual* model objects to the existing React results-model.ts contract.

No resident IDs, row-level profiles, policy verdicts, or invented RAG text leave here.
Unmapped group gap fields are null, never manufactured.
"""
from __future__ import annotations
from collections import Counter
from lastmile_ai.schemas import (
    AccessibilityStatus, ChannelID, DeliveryStatus, RESIDENT_COUNT,
    SimulationConfiguration,
)
from lastmile_ai.recovery_runtime import RecoveryRun
from .contract import TO_WEB


def _metric(n: int | float, unit: str = 'residents') -> dict:
    return {'value': n, 'unit': unit}


def _channel_counts(delivery) -> list[dict]:
    results = []
    # Only selected_delivery_records are actual plan assignments; never potential_channel_evaluations.
    for channel in ChannelID:
        selected = [r for r in delivery.selected_delivery_records if r.channel_id == channel]
        statuses = Counter(r.status for r in selected)
        attempted = sum(bool(r.attempted) for r in selected)
        assert attempted == sum(statuses[x] for x in (
            DeliveryStatus.DELIVERED, DeliveryStatus.DELAYED, DeliveryStatus.FAILED
        )), 'Selected attempts/statuses disagree'
        results.append({
            'id': channel.value,
            'selectedAttempts': attempted,
            'delivered': statuses[DeliveryStatus.DELIVERED],
            'delayed': statuses[DeliveryStatus.DELAYED],
            'failed': statuses[DeliveryStatus.FAILED],
            'unavailable': statuses[DeliveryStatus.UNAVAILABLE],
        })
    return results


def _accessibility(assessment, residents) -> dict:
    """Only separately evidenced *review* group counts; no inferred unique gap KPI."""
    review_ids = {f.resident_id for f in assessment.accessibility_findings
                  if f.status == AccessibilityStatus.REVIEW}
    groups = (
        ('hearing', 'hearing_impairment'),
        ('visual', 'visual_impairment'),
        ('elderly', 'elderly_65_plus'),
        ('connectivity', 'limited_internet'),
    )
    return {
        'uniqueResidentsWithGaps': None,
        'groups': [{'id': name,
                    'residentsRequiringReview': sum(
                        1 for r in residents if getattr(r, field) and r.resident_id in review_ids
                    )} for name, field in groups],
    }


def _normalized_plan(plan_id, metrics, delivery, assessment, residents, baseline_metrics):
    assert metrics.plan_id == delivery.plan_id == assessment.plan_id == plan_id
    # Report recovery as the fraction of the *fixed 1,000 residents* gaining
    # effective coverage vs P0, not a relative percentage increase from P0.
    recovery_population_percent = round(
        100 * (metrics.effective_coverage_count - baseline_metrics.effective_coverage_count)
        / RESIDENT_COUNT, 6)
    return {
        'id': plan_id,
        'metrics': {
            'reach': _metric(metrics.estimated_reach_count),
            'effective': _metric(metrics.effective_coverage_count),
            'recovery': (_metric(recovery_population_percent, 'percent')
                         if recovery_population_percent >= 0 else None),
            'critical': _metric(metrics.unresolved_critical_count),
        },
        'accessibility': _accessibility(assessment, residents),
        'channels': _channel_counts(delivery),
    }


def normalize_result(run: RecoveryRun, config: SimulationConfiguration, eval_id: str) -> dict:
    """Build data accepted by the existing evaluationSchema (Zod)."""
    if run.baseline.metrics.plan_id != 'P0':
        raise ValueError('Missing baseline P0')
    if run.recovery.baseline_metrics != run.baseline.metrics:
        raise ValueError('Recovery baseline mismatch')
    residents = run.baseline.residents
    plans = [_normalized_plan(
        'P0', run.baseline.metrics, run.baseline.delivery,
        run.baseline.accessibility, residents, run.baseline.metrics,
    )]
    seen = {'P0'}
    for candidate in run.tested_plans:
        if candidate.plan_id in seen:
            raise ValueError('Duplicate evaluated candidate')
        seen.add(candidate.plan_id)
        plans.append(_normalized_plan(
            candidate.plan_id, candidate.metrics, candidate.delivery,
            candidate.accessibility, residents, run.baseline.metrics,
        ))
    if run.recovery.recommended_plan_id not in seen:
        raise ValueError('Recommended plan was not evaluated')

    # The explanation is an actual Agent 4 explanation, *not* RAG.
    # Arabic translation is absent; the UI must not invent one.
    explanation = {
        'source': 'backend',
        'reason': {'ar': None, 'en': run.recovery.explanation},
        'improvements': [],
        'accessibility': [],
        'unresolved': None,
        'tradeoffs': [],
        'limitations': [],
    }
    if run.recovery.unresolved_review_notes:
        explanation['unresolved'] = {
            'ar': None, 'en': '; '.join(run.recovery.unresolved_review_notes),
        }
    return {
        'id': eval_id,
        'source': 'backend',
        'configuration': {
            'scenario': 'AL_WADI_FLASH_FLOOD',
            'stage': TO_WEB[config.selected_stage],
            'enabledChannelIds': [c.value for c in config.enabled_channels],
            'population': RESIDENT_COUNT,
        },
        'plans': plans,
        'recommendedPlanId': run.recovery.recommended_plan_id,
        'explanation': explanation,
    }


def simulation_summary(result: dict) -> dict:
    """Typed UI panels use actual aggregates. No unverified agent progress."""
    by_id = {p['id']: p for p in result['plans']}
    p0 = by_id['P0']
    final = by_id[result['recommendedPlanId']]
    def m(p, key):
        return p['metrics'][key]['value']
    return {
        'id': result['id'],
        'configuration': {
            'scenario': result['configuration']['scenario'],
            'stage': result['configuration']['stage'],
            'enabledChannelIds': result['configuration']['enabledChannelIds'],
        },
        'outputs': {
            'delivery': [{'label': 'P0 estimated technical reach',
                          'detail': f'{m(p0, "reach")} of {RESIDENT_COUNT} synthetic residents'}],
            'risk': [{'label': 'P0 unresolved critical cases',
                      'detail': f'{m(p0, "critical")} unique residents'}],
            'accessibility': [{'label': 'P0 effective warning coverage',
                               'detail': f'{m(p0, "effective")} unique residents'}],
            'policy': [],  # No automatic legal verdict.
            'recovery': [{'label': f'Selected plan: {result["recommendedPlanId"]}',
                          'detail': f'Estimated reach {m(final,"reach")}; effective coverage {m(final,"effective")}'}],
            'trace': [{'label': 'Evaluated plans',
                       'detail': ', '.join(p['id'] for p in result['plans'])}],
        },
    }
