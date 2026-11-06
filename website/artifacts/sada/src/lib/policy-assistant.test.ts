import { describe, expect, it } from 'vitest';
import { policyResponse } from './policy-assistant';

const citation = { passage_id: 'SRC-01-E01', source_id: 'SRC-01', section: 'instruction',
  official_url: 'https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html' };
// Contract fixtures only. These are NOT real model outputs.
const fixture = {
  retrieval: { status: 'EVIDENCE_FOUND', evidence_items: [{
    ...citation, evidence_id: citation.passage_id, source_title: 'CAP', text: 'Source excerpt',
  }] },
  explanation: { schema_version: 'ai_explanation.v1', question: 'Question',
    status: 'Answered', answer: 'Contract fixture [SRC-01-E01]', model_id: 'qwen/qwen-2.5-7b-instruct',
    llm_invoked: true, execution_mode: 'live_llm', limitations: [], citations: [citation] },
};
describe('AI display provenance contract', () => {
  it('accepts original field names and linked evidence IDs', () => {
    expect(policyResponse.safeParse(fixture).success).toBe(true);
  });
  it('refuses a claimed answer without actual invocation or valid citations', () => {
    for (const override of [{ llm_invoked: false }, { execution_mode: 'fallback' },
      { model_id: 'qwen2.5:3b' }, { model_id: 'unapproved/model' },
      { citations: [] }, { citations: [{ ...citation, passage_id: 'INVENTED' }] }]) {
      expect(policyResponse.safeParse({ ...fixture,
        explanation: { ...fixture.explanation, ...override } }).success).toBe(false);
    }
  });
  it('accepts honest unavailable and insufficient states without fabricated answers', () => {
    for (const status of ['ModelUnavailable', 'InsufficientInformation', 'ReviewRequired']) {
      expect(policyResponse.safeParse({ ...fixture, explanation: {
        ...fixture.explanation, status, answer: '', model_id: null, llm_invoked: false,
        execution_mode: 'fallback', citations: [],
      } }).success).toBe(true);
    }
  });
  it('does not permit unsafe source links', () => {
    expect(policyResponse.safeParse({ ...fixture, retrieval: { ...fixture.retrieval,
      evidence_items: [{ ...fixture.retrieval.evidence_items[0], official_url: 'javascript:alert(1)' }],
    } }).success).toBe(false);
  });
});
