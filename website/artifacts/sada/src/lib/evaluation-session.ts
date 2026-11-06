import { z } from 'zod';

export const evaluationSessionKey = 'sada-last-evaluation';
const savedEvaluationSchema = z.object({
  // guid preserves Zod 3's UUID-shaped acceptance (including legacy versions).
  id: z.guid(),
  selectionKey: z.string(),
});

export function readSavedEvaluation() {
  try {
    return savedEvaluationSchema.parse(JSON.parse(localStorage.getItem(evaluationSessionKey) ?? 'null'));
  } catch { return null; }
}

export function readSavedEvaluationId() {
  return readSavedEvaluation()?.id ?? null;
}

export function saveEvaluation(id: string, selectionKey: string) {
  try {
    localStorage.setItem(evaluationSessionKey, JSON.stringify({ id, selectionKey }));
  } catch { /* URL and current session still work if browser storage is blocked. */ }
}

export function clearSavedEvaluation() {
  try { localStorage.removeItem(evaluationSessionKey); } catch { /* Storage is optional. */ }
}
