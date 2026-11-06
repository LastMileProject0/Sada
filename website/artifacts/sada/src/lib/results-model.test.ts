import assert from 'node:assert/strict';
import { test } from 'node:test';
import { evaluationSchema, groupReviewCount, metricChange } from './results-model';
import { verifiedResultsDemo } from './results-demo';

test('partial verified fixture contains only confirmed P0 and P3 resident metrics', () => {
  assert.equal(verifiedResultsDemo.source, 'verified_demo');
  assert.equal(verifiedResultsDemo.configuration.stage, 'T+04');
  assert.deepEqual(verifiedResultsDemo.configuration.enabledChannelIds, ['CH01', 'CH02', 'CH03', 'CH04', 'CH05']);
  assert.deepEqual(verifiedResultsDemo.plans.map(p => p.id), ['P0', 'P3']);
  const [baseline, final] = verifiedResultsDemo.plans;
  assert.deepEqual([baseline.metrics.reach?.value, final.metrics.reach?.value], [722, 942]);
  assert.deepEqual([baseline.metrics.effective?.value, final.metrics.effective?.value], [0, 366]);
  for (const plan of verifiedResultsDemo.plans) {
    assert.equal(plan.metrics.effective?.unit, 'residents');
    assert.equal(plan.metrics.critical, null);
    assert.equal(plan.metrics.recovery, null);
    assert.equal(plan.accessibility, null);
    assert.deepEqual(plan.channels, []);
  }
  assert.equal(verifiedResultsDemo.recommendedPlanId, 'P3');
  assert.equal(verifiedResultsDemo.explanation, null);
});

test('missing metrics are not zero; deltas require equal units', () => {
  assert.equal(metricChange(null, { value: 1, unit: 'residents' }, 'reach'), null);
  assert.equal(metricChange({ value: 10, unit: 'percent' }, { value: 12, unit: 'residents' }, 'reach'), null);
});

test('absolute increase from a zero baseline is valid, relative percentage is not', () => {
  assert.deepEqual(metricChange(
    { value: 0, unit: 'residents' }, { value: 366, unit: 'residents' }, 'effective',
  ), { difference: 366, unit: 'residents', relativePercent: null, improved: true });
});

test('rate differences are percentage points and fewer critical cases is an improvement', () => {
  assert.equal(metricChange({ value: 50, unit: 'percent' }, { value: 65, unit: 'percent' }, 'effective')?.unit, 'pp');
  assert.equal(metricChange({ value: 30, unit: 'residents' }, { value: 20, unit: 'residents' }, 'critical')?.improved, true);
  assert.equal(metricChange({ value: 30, unit: 'residents' }, { value: 40, unit: 'residents' }, 'critical')?.improved, false);
});

test('unique aggregate stays distinct from overlapping group counts', () => {
  const result = structuredClone(verifiedResultsDemo);
  result.plans[0].accessibility = {
    uniqueResidentsWithGaps: 12,
    groups: [{ id: 'hearing', residentsRequiringReview: 8 }, { id: 'visual', residentsRequiringReview: 9 }],
  };
  const normalized = evaluationSchema.parse(result);
  assert.equal(normalized.plans[0].accessibility?.uniqueResidentsWithGaps, 12);
  assert.equal(groupReviewCount(normalized.plans[0], 'hearing'), 8);
  assert.equal(groupReviewCount(normalized.plans[0], 'elderly'), null);
});

test('reject unknown plans, unsupported channels, duplicate IDs and invalid values', () => {
  for (const mutate of [
    (r: typeof verifiedResultsDemo) => { r.recommendedPlanId = 'P1'; },
    (r: typeof verifiedResultsDemo) => { r.plans.push(r.plans[0]); },
    (r: typeof verifiedResultsDemo) => { r.plans[0].metrics.reach = { value: 1001, unit: 'residents' }; },
    (r: typeof verifiedResultsDemo) => { r.plans[0].metrics.effective = { value: 110, unit: 'percent' }; },
    (r: typeof verifiedResultsDemo) => { r.plans[0].metrics.critical = { value: -1, unit: 'residents' }; },
  ]) {
    const invalid = structuredClone(verifiedResultsDemo);
    mutate(invalid);
    assert.equal(evaluationSchema.safeParse(invalid).success, false);
  }
  const invalidChannel = { ...verifiedResultsDemo, configuration: { ...verifiedResultsDemo.configuration, enabledChannelIds: ['CELL_BROADCAST'] } };
  assert.equal(evaluationSchema.safeParse(invalidChannel).success, false);
});
