import { useEffect, useRef, useState } from 'react';
import { usePlanning, type ChannelId, type Stage } from '@/lib/planning-state';
import { clearSavedEvaluation, readSavedEvaluation, saveEvaluation } from './evaluation-session';

export interface SimulationConfig {
  scenario: 'AL_WADI_FLASH_FLOOD';
  stage: Stage;
  enabledChannelIds: ChannelId[];
}

export interface SimulationOutput {
  label: string;
  detail: string;
}

export interface SimulationResult {
  id: string;
  configuration: SimulationConfig;
  outputs: Record<'delivery' | 'risk' | 'accessibility' | 'policy' | 'recovery' | 'trace', SimulationOutput[]>;
}

export type ExecutionStatus = 'not_started' | 'restoring' | 'running' | 'completed' | 'error';

/** The Python integration belongs here, not in presentation components.
 * A real adapter must validate responses and preserve deterministic outcomes.
 * RAG explanations must never mutate the evaluation result.
 */
export interface SimulationAdapter {
  available: boolean;
  evaluate: (configuration: SimulationConfig, signal: AbortSignal) => Promise<SimulationResult>;
  restore?: (id: string, signal: AbortSignal) => Promise<SimulationResult>;
}

const pendingAdapter: SimulationAdapter = {
  available: false,
  async evaluate() {
    throw new Error('simulation_integration_pending');
  },
};

export function useSimulation(adapter: SimulationAdapter = pendingAdapter) {
  const { stage, enabledChannels, evaluationPending, clearPending } = usePlanning();
  const [status, setStatus] = useState<ExecutionStatus>('not_started');
  const [integrationPending, setIntegrationPending] = useState(!adapter.available);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const request = useRef<AbortController | null>(null);
  const selectionKey = `${stage}:${enabledChannels.join(',')}`;
  const previousSelection = useRef(selectionKey);
  // Updated during render so an old result cannot become visible for a new config.
  const latestSelection = useRef(selectionKey);
  latestSelection.current = selectionKey;

  function reset() {
    request.current?.abort();
    request.current = null;
    setStatus('not_started');
    setIntegrationPending(!adapter.available);
    setError(null);
    setResult(null);
    clearSavedEvaluation();
    clearPending();
  }

  useEffect(() => {
    if (previousSelection.current !== selectionKey) {
      previousSelection.current = selectionKey;
      reset();
    }
  }, [selectionKey]);

  useEffect(() => () => request.current?.abort(), []);

  useEffect(() => {
    const saved = readSavedEvaluation();
    if (evaluationPending || !saved || saved.selectionKey !== selectionKey || !adapter.restore) return;
    const controller = new AbortController();
    request.current = controller;
    setStatus('restoring');
    void adapter.restore(saved.id, controller.signal).then(response => {
      if (controller.signal.aborted || latestSelection.current !== selectionKey) return;
      if (response.id !== saved.id || response.configuration.stage !== stage ||
        response.configuration.enabledChannelIds.join(',') !== enabledChannels.join(',')) {
        throw new Error('simulation_invalid_response');
      }
      setResult(response);
      setStatus('completed');
    }).catch(() => {
      if (!controller.signal.aborted) {
        setError('simulation_error');
        setStatus('error');
      }
    }).finally(() => {
      if (request.current === controller) request.current = null;
    });
    return () => controller.abort();
  }, [adapter, selectionKey]);

  useEffect(() => {
    if (!evaluationPending) return;
    clearPending();
    void start();
  }, [evaluationPending]);

  async function start() {
    if (request.current) return;
    setError(null);
    setResult(null);
    if (!adapter.available) {
      // Never simulate Running, completion, agent progress or outputs locally.
      setStatus('not_started');
      setIntegrationPending(true);
      return;
    }
    const controller = new AbortController();
    request.current = controller;
    clearSavedEvaluation();
    const submittedKey = selectionKey;
    const configuration: SimulationConfig = {
      scenario: 'AL_WADI_FLASH_FLOOD', stage,
      enabledChannelIds: [...enabledChannels],
    };
    setIntegrationPending(false);
    setStatus('running');
    try {
      const response = await adapter.evaluate(configuration, controller.signal);
      if (controller.signal.aborted || latestSelection.current !== submittedKey) return;
      if (!response.id || response.configuration.scenario !== configuration.scenario ||
        response.configuration.stage !== stage ||
        response.configuration.enabledChannelIds.join(',') !== configuration.enabledChannelIds.join(',')) {
        throw new Error('simulation_invalid_response');
      }
      setResult(response);
      setStatus('completed');
      saveEvaluation(response.id, submittedKey);
    } catch {
      if (!controller.signal.aborted && latestSelection.current === submittedKey) {
        // Translation keys only; never expose raw service errors as UI copy.
        setError('simulation_error');
        setStatus('error');
      }
    } finally {
      if (request.current === controller) request.current = null;
    }
  }

  return { status, integrationPending, error, result, start, reset };
}
