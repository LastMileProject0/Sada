import { z } from 'zod';

const source = z.object({
  evidence_id: z.string(), source_id: z.string(), source_title: z.string(),
  section: z.string(), official_url: z.string().url().refine(u => u.startsWith('https://')),
  text: z.string(), pdf_page: z.number().nullable().optional(),
});
export const policyResponse = z.object({
  retrieval: z.object({
    status: z.enum(['EVIDENCE_FOUND', 'INSUFFICIENT_EVIDENCE']),
    evidence_items: z.array(source).max(4),
  }),
  explanation: z.object({
    schema_version: z.literal('ai_explanation.v1'),
    question: z.string(),
    status: z.enum(['Answered', 'ReviewRequired', 'InsufficientInformation', 'ModelUnavailable']),
    answer: z.string(), model_id: z.string().nullable(), llm_invoked: z.boolean(),
    execution_mode: z.string(), limitations: z.array(z.string()),
    citations: z.array(z.object({
      passage_id: z.string(), source_id: z.string(), section: z.string(),
      official_url: z.string().url().refine(u => u.startsWith('https://')),
    })),
  }),
}).superRefine((value, context) => {
  if (value.explanation.status === 'Answered' && (
    !value.explanation.llm_invoked || value.explanation.execution_mode !== 'live_llm' ||
    value.explanation.model_id !== 'qwen/qwen-2.5-7b-instruct' || !value.explanation.citations.length ||
    !value.explanation.answer.trim() || value.explanation.citations.some(c =>
      !value.retrieval.evidence_items.some(e => e.evidence_id === c.passage_id
        && e.source_id === c.source_id && e.official_url === c.official_url))
  )) context.addIssue({ code: z.ZodIssueCode.custom, message: 'Unverified AI answer' });
});
export type PolicyResponse = z.infer<typeof policyResponse>;

export async function askPolicy(question: string, signal: AbortSignal): Promise<PolicyResponse> {
  const response = await fetch(`${import.meta.env.BASE_URL}api/policy/explain`, {
    method: 'POST', credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }), signal,
  });
  if (!response.ok) {
    throw new Error(response.status === 429 ? 'limited'
      : response.status === 503 ? 'unavailable' : 'failed');
  }
  return policyResponse.parse(await response.json());
}
