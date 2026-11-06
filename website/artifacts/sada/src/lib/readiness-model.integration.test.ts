import { describe, expect, it } from 'vitest';
import { verifiedResultsDemo } from './results-demo';
import { authorizedReadinessEvaluation, readinessPlans } from './readiness-model';

describe('readiness authorization and projection boundary', () => {
  const fixture = () => ({ ...structuredClone(verifiedResultsDemo), source: 'backend' as const });
  it('accepts only an exact backend record match', () => {
    const data = fixture();
    expect(authorizedReadinessEvaluation(data, data.id)?.id).toBe(data.id);
    expect(authorizedReadinessEvaluation(data, 'another-id')).toBeNull();
    expect(authorizedReadinessEvaluation(data, null)).toBeNull();
    expect(authorizedReadinessEvaluation(verifiedResultsDemo, verifiedResultsDemo.id)).toBeNull();
    expect(authorizedReadinessEvaluation({ ...data, plans: [] }, data.id)).toBeNull();
  });
  it('never invents a recommendation or substitutes the last plan', () => {
    const data = fixture();
    data.recommendedPlanId = null;
    expect(readinessPlans(data).recommended).toBeNull();
    expect(readinessPlans(data).baseline.id).toBe('P0');
    data.recommendedPlanId = 'P0';
    expect(readinessPlans(data).recommended?.id).toBe('P0');
  });
  it('preserves unavailable metrics and overlapping group counts unchanged', () => {
    const data = fixture();
    const parsed = authorizedReadinessEvaluation(data, data.id)!;
    expect(parsed).toEqual(data);
    const before = JSON.stringify(data);
    readinessPlans(parsed);
    expect(JSON.stringify(data)).toBe(before);
  });
});
