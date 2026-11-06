import { afterEach, describe, expect, it, vi } from 'vitest';
import { z } from 'zod';
import { evaluationSchema } from './results-model';
import { verifiedResultsDemo } from './results-demo';
import { evaluationSessionKey, readSavedEvaluation } from './evaluation-session';
import { sadaSimulationAdapter } from './sada-api-adapters';
import { policyResponse } from './policy-assistant';

afterEach(() => { localStorage.clear(); vi.unstubAllGlobals(); });

describe('patched Zod compatibility boundary', () => {
  it('preserves existing normalized results, unknown-key stripping, and bilingual text', () => {
    const value = structuredClone(verifiedResultsDemo);
    value.explanation = { source: 'backend', reason: { ar: 'اختبار', en: 'Test' },
      improvements: [], accessibility: [], unresolved: null, tradeoffs: [], limitations: [] };
    expect(evaluationSchema.parse({ ...value, untrustedExtra: 'discard' })).toEqual(value);
  });

  it.each(['11111111-1111-4111-8111-111111111111',
    '00000000-0000-0000-0000-000000000000', 'ABCDEFAB-1234-0123-0123-ABCDEFABCDEF'])(
    'preserves former UUID shape semantics for saved state and API replies: %s', async id => {
      const saved = { id, selectionKey: 'T+04:CH01' };
      localStorage.setItem(evaluationSessionKey, JSON.stringify(saved));
      expect(readSavedEvaluation()).toEqual(saved);
      const configuration = { scenario: 'AL_WADI_FLASH_FLOOD' as const,
        stage: 'T+04' as const, enabledChannelIds: ['CH01' as const] };
      const reply = { id, configuration, outputs: {
        delivery: [], risk: [], accessibility: [], policy: [], recovery: [], trace: [],
      } };
      vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(reply))));
      expect(await sadaSimulationAdapter.evaluate(configuration, new AbortController().signal))
        .toEqual(reply);
    });

  it.each([null, {}, [], { id: ['malformed'], selectionKey: 'x' },
    { id: 'not-a-uuid', selectionKey: 'x' }])('fails closed on malformed saved state %j', value => {
      localStorage.setItem(evaluationSessionKey, JSON.stringify(value));
      expect(readSavedEvaluation()).toBeNull();
    });

  it('rejects invalid numbers and preserves nullable/missing-value distinctions', () => {
    for (const value of [NaN, Infinity, -1, 1001, 1.5]) {
      const input = structuredClone(verifiedResultsDemo);
      input.plans[0].metrics.reach = { value, unit: 'residents' };
      expect(evaluationSchema.safeParse(input).success).toBe(false);
    }
    const input = structuredClone(verifiedResultsDemo);
    input.plans[0].metrics.reach = null;
    expect(evaluationSchema.parse(input).plans[0].metrics.reach).toBeNull();
    const missing = JSON.parse(JSON.stringify(input));
    delete missing.plans[0].metrics.reach;
    expect(evaluationSchema.safeParse(missing).success).toBe(false);
  });

  it('does not silently tighten the former integer-count contract', () => {
    const input = structuredClone(verifiedResultsDemo);
    input.plans[0].channels = [{ id: 'CH01', selectedAttempts: 2 ** 53,
      delivered: 0, delayed: null, failed: null, unavailable: null }];
    expect(evaluationSchema.parse(input).plans[0].channels[0].selectedAttempts).toBe(2 ** 53);
    input.plans[0].channels[0].selectedAttempts = 1.5;
    expect(evaluationSchema.safeParse(input).success).toBe(false);
  });

  it('patched bounded arrays reject size before examining hostile elements', () => {
    const values = Array(10_000).fill(null);
    // A throwing accessor proves no element is evaluated, without stressing memory.
    Object.defineProperty(values, 0, { get() { throw new Error('Element must not be read'); } });
    const guarded = z.array(z.string()).max(4).safeParse(values);
    expect(guarded.success).toBe(false);
    if (!guarded.success) expect(guarded.error.issues).toHaveLength(1);
    const policy = policyResponse.safeParse({
      retrieval: { status: 'EVIDENCE_FOUND', evidence_items: values },
      explanation: { schema_version: 'ai_explanation.v1', question: 'Synthetic',
        status: 'ReviewRequired', answer: '', model_id: null, llm_invoked: false,
        execution_mode: 'fallback', limitations: [], citations: [] },
    });
    expect(policy.success).toBe(false);
    if (!policy.success) {
      expect(policy.error.issues).toHaveLength(1);
      expect(policy.error.issues[0].path).toEqual(['retrieval', 'evidence_items']);
    }
  });
});
