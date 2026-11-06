import { useEffect, useState } from 'react';
import { evaluationSchema, type EvaluationResult } from './results-model';
import { verifiedResultsDemo } from './results-demo';

/** Future FastAPI boundary. The dashboard never interprets query parameters as results. */
export interface ResultsAdapter {
  available: boolean;
  load: (evaluationId: string, signal: AbortSignal) => Promise<unknown>;
}
const disconnected: ResultsAdapter = {
  available: false,
  async load() { throw new Error('Results integration pending'); },
};

export function useResults(evaluationId: string | null, adapter: ResultsAdapter = disconnected) {
  const [mode, setMode] = useState<'live' | 'demo'>('live');
  const [record, setRecord] = useState<{ id: string; data: EvaluationResult } | null>(null);
  const [state, setState] = useState<'empty' | 'loading' | 'ready' | 'error'>('empty');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    setRecord(null);
    setState('empty');
    if (!evaluationId || !adapter.available || mode === 'demo') return;
    const controller = new AbortController();
    setState('loading');
    void (async () => {
      try {
        const value = await adapter.load(evaluationId, controller.signal);
        if (controller.signal.aborted) return;
        const result = evaluationSchema.parse(value);
        if (result.id !== evaluationId || result.source !== 'backend') throw new Error('Invalid evaluation result');
        setRecord({ id: evaluationId, data: result });
        setState('ready');
      } catch {
        if (!controller.signal.aborted) { setRecord(null); setState('error'); }
      }
    })();
    return () => controller.abort();
  }, [evaluationId, adapter, mode, retry]);
  const data = mode === 'demo' ? verifiedResultsDemo : record?.id === evaluationId ? record.data : null;
  return {
    data, mode,
    status: mode === 'demo' ? 'ready' as const : state,
    integrationPending: !adapter.available,
    showDemo: () => setMode('demo'),
    showLive: () => setMode('live'),
    retry: () => setRetry(n => n + 1),
  };
}
