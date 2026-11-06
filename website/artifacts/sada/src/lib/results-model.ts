import { z } from 'zod';
import { CHANNEL_IDS, STAGES } from './planning-state';

// Zod 4 int() also imposes a safe-integer range; preserve the former contract.
const optionalCount = z.number().nonnegative().refine(Number.isInteger, 'Expected integer').nullable();
export const metricKeys = ['reach', 'effective', 'recovery', 'critical'] as const;
export type MetricKey = typeof metricKeys[number];
export const groupIds = ['hearing', 'visual', 'elderly', 'connectivity'] as const;
export type GroupId = typeof groupIds[number];
const metricSchema = z.object({
  value: z.number().finite().nonnegative(),
  unit: z.enum(['residents', 'percent']),
}).refine(m => m.unit !== 'percent' || m.value <= 100, 'Percent must be between 0 and 100');
export type ResultMetric = z.infer<typeof metricSchema>;
const localizedText = z.object({ ar: z.string().nullable(), en: z.string().nullable() });
const channelSchema = z.object({
  id: z.enum(CHANNEL_IDS),
  selectedAttempts: optionalCount,
  delivered: optionalCount,
  delayed: optionalCount,
  failed: optionalCount,
  unavailable: optionalCount,
});
export type ChannelPerformance = z.infer<typeof channelSchema>;
const accessibilitySchema = z.object({
  uniqueResidentsWithGaps: optionalCount,
  groups: z.array(z.object({
    id: z.enum(groupIds),
    residentsRequiringReview: optionalCount,
  })),
});
export const evaluatedPlanSchema = z.object({
  id: z.enum(['P0', 'P1', 'P2', 'P3']),
  metrics: z.object({
    reach: metricSchema.nullable(),
    effective: metricSchema.nullable(),
    recovery: metricSchema.nullable(),
    critical: metricSchema.nullable(),
  }),
  accessibility: accessibilitySchema.nullable(),
  channels: z.array(channelSchema),
});
export type EvaluatedPlan = z.infer<typeof evaluatedPlanSchema>;
export const evaluationSchema = z.object({
  id: z.string().min(1),
  source: z.enum(['backend', 'verified_demo']),
  configuration: z.object({
    scenario: z.literal('AL_WADI_FLASH_FLOOD'),
    stage: z.enum(STAGES),
    enabledChannelIds: z.array(z.enum(CHANNEL_IDS)).min(1),
    population: z.literal(1000),
  }),
  plans: z.array(evaluatedPlanSchema).min(1),
  recommendedPlanId: z.enum(['P0', 'P1', 'P2', 'P3']).nullable(),
  explanation: z.object({
    source: z.enum(['backend', 'rag']),
    reason: localizedText.nullable(),
    improvements: z.array(localizedText),
    accessibility: z.array(localizedText),
    unresolved: localizedText.nullable(),
    tradeoffs: z.array(localizedText),
    limitations: z.array(localizedText),
  }).nullable(),
}).superRefine((data, ctx) => {
  const ids = data.plans.map(p => p.id);
  if (new Set(ids).size !== ids.length || !ids.includes('P0')) {
    ctx.addIssue({ code: 'custom', message: 'An evaluation must contain one P0 baseline and unique plan IDs' });
  }
  if (data.recommendedPlanId && !ids.includes(data.recommendedPlanId)) {
    ctx.addIssue({ code: 'custom', message: 'Recommendation must reference an evaluated plan' });
  }
  if (new Set(data.configuration.enabledChannelIds).size !== data.configuration.enabledChannelIds.length) {
    ctx.addIssue({ code: 'custom', message: 'Enabled channels must be unique' });
  }
  for (const plan of data.plans) {
    if (new Set(plan.channels.map(c => c.id)).size !== plan.channels.length) {
      ctx.addIssue({ code: 'custom', message: 'Channel outcomes must be unique within a plan' });
    }
    if (plan.accessibility) {
      if (new Set(plan.accessibility.groups.map(g => g.id)).size !== plan.accessibility.groups.length) {
        ctx.addIssue({ code: 'custom', message: 'Accessibility group IDs must be unique' });
      }
      const counts = [
        plan.accessibility.uniqueResidentsWithGaps,
        ...plan.accessibility.groups.map(g => g.residentsRequiringReview),
      ];
      if (counts.some(n => n !== null && n > data.configuration.population)) {
        ctx.addIssue({ code: 'custom', message: 'Unique resident counts exceed the synthetic population' });
      }
    }
    for (const metric of Object.values(plan.metrics)) {
      if (metric?.unit === 'residents' && (!Number.isInteger(metric.value) || metric.value > data.configuration.population)) {
        ctx.addIssue({ code: 'custom', message: 'Resident metric must be a unique population count' });
      }
    }
  }
});
export type EvaluationResult = z.infer<typeof evaluationSchema>;

/** Deltas compare equal units only. A zero baseline never yields a relative percentage. */
export function metricChange(baseline: ResultMetric | null | undefined, final: ResultMetric | null | undefined, key: MetricKey) {
  if (!baseline || !final || baseline.unit !== final.unit) return null;
  const difference = final.value - baseline.value;
  return {
    difference,
    unit: final.unit === 'percent' ? 'pp' as const : 'residents' as const,
    relativePercent: baseline.value === 0 ? null : difference / baseline.value * 100,
    improved: key === 'critical' ? difference < 0 : difference > 0,
  };
}

/** Groups may overlap: never sum these into the unique-resident aggregate. */
export function groupReviewCount(plan: EvaluatedPlan | null, id: GroupId) {
  return plan?.accessibility?.groups.find(g => g.id === id)?.residentsRequiringReview ?? null;
}
