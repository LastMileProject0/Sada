import { evaluationSchema, type EvaluationResult } from './results-model';

/** A URL/session identifier selects a record; only the ownership-protected GET authorizes it. */
export function authorizedReadinessEvaluation(value: unknown, evaluationId: string | null): EvaluationResult | null {
  if (!evaluationId) return null;
  const parsed = evaluationSchema.safeParse(value);
  return parsed.success && parsed.data.source === 'backend' && parsed.data.id === evaluationId
    ? parsed.data : null;
}

/** Never substitute the last/best-looking plan when the engine supplies no recommendation. */
export function readinessPlans(data: EvaluationResult) {
  return {
    baseline: data.plans.find(plan => plan.id === 'P0')!,
    recommended: data.recommendedPlanId
      ? data.plans.find(plan => plan.id === data.recommendedPlanId) ?? null : null,
  };
}
