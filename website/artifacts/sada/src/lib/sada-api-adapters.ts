/** Same-origin bridge to the existing sada_bridge FastAPI contract. */
import { z } from 'zod';
import { CHANNEL_IDS, STAGES } from './planning-state';
import type { SimulationAdapter } from './simulation';
import type { ResultsAdapter } from './results-state';
import { evaluationSchema, type EvaluationResult } from './results-model';

const apiUrl = `${import.meta.env.BASE_URL}api/evaluations`;
const itemSchema = z.object({ label: z.string(), detail: z.string() });
const outputSchema = z.object({
  delivery: z.array(itemSchema),
  risk: z.array(itemSchema),
  accessibility: z.array(itemSchema),
  policy: z.array(itemSchema),
  recovery: z.array(itemSchema),
  trace: z.array(itemSchema),
});
const simulationSchema = z.object({
  // Match the former UUID shape check; do not tighten the API contract.
  id: z.guid(),
  configuration: z.object({
    scenario: z.literal('AL_WADI_FLASH_FLOOD'),
    stage: z.enum(STAGES),
    enabledChannelIds: z.array(z.enum(CHANNEL_IDS)).min(1),
  }),
  outputs: outputSchema,
});

async function jsonOrThrow(response: Response): Promise<unknown> {
  if (!response.ok) throw new Error('sada_backend_unavailable_or_failed');
  return response.json() as Promise<unknown>;
}

/** Display projection of stored aggregates, never a simulation or recommendation. */
function restoredSummary(result: EvaluationResult) {
  const baseline = result.plans.find(p => p.id === 'P0');
  const final = result.plans.find(p => p.id === result.recommendedPlanId);
  const count = (value: number | undefined) => value === undefined ? [] : [{ label: 'P0', detail: String(value) }];
  return {
    delivery: count(baseline?.metrics.reach?.value),
    risk: count(baseline?.metrics.critical?.value),
    accessibility: count(baseline?.metrics.effective?.value),
    policy: [],
    recovery: final ? [{ label: final.id, detail: [
      final.metrics.reach?.value, final.metrics.effective?.value,
    ].filter(v => v !== undefined).join(' / ') }] : [],
    trace: [{ label: 'P0–P3', detail: result.plans.map(p => p.id).join(', ') }],
  };
}

export const sadaSimulationAdapter: SimulationAdapter = {
  available: true,
  async evaluate(configuration, signal) {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(configuration),
      signal,
    });
    return simulationSchema.parse(await jsonOrThrow(response));
  },
  async restore(evaluationId, signal) {
    const result = evaluationSchema.parse(await sadaResultsAdapter.load(evaluationId, signal));
    if (result.id !== evaluationId || result.source !== 'backend') throw new Error('simulation_invalid_response');
    // Restore confirmed execution, not cached metrics or invented agent outputs.
    return { id: result.id, configuration: result.configuration,
      outputs: restoredSummary(result) };
  },
};

export const sadaResultsAdapter: ResultsAdapter = {
  available: true,
  async load(evaluationId, signal) {
    // The existing useResults() performs full evaluationSchema parsing.
    const response = await fetch(`${apiUrl}/${encodeURIComponent(evaluationId)}`, { signal });
    return jsonOrThrow(response);
  },
};
