import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PlanningProvider, usePlanning, planningStorageKey, evaluationHandoffKey } from './planning-state';
import { useSimulation, type SimulationAdapter, type SimulationConfig, type SimulationResult } from './simulation';
import { evaluationSessionKey } from './evaluation-session';
import { sadaResultsAdapter, sadaSimulationAdapter } from './sada-api-adapters';

const id = '11111111-1111-4111-8111-111111111111';
const config: SimulationConfig = {
  scenario: 'AL_WADI_FLASH_FLOOD', stage: 'T+04',
  enabledChannelIds: ['CH01', 'CH02', 'CH03', 'CH04', 'CH05'],
};
const response: SimulationResult = { id, configuration: config,
  outputs: { delivery: [], risk: [], accessibility: [], policy: [], recovery: [], trace: [] } };
let root: Root;
let container: HTMLDivElement;
let sim: ReturnType<typeof useSimulation>;
let planning: ReturnType<typeof usePlanning>;

function Probe({ adapter }: { adapter: SimulationAdapter }) {
  sim = useSimulation(adapter);
  planning = usePlanning();
  return null;
}
async function mount(adapter: SimulationAdapter) {
  container = document.createElement('div');
  document.body.append(container);
  root = createRoot(container);
  await act(async () => { root.render(createElement(PlanningProvider, {
    children: createElement(Probe, { adapter }),
  })); });
}
beforeEach(() => {
  Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });
  localStorage.clear();
  localStorage.setItem(planningStorageKey, JSON.stringify({
    stage: config.stage, enabledChannels: config.enabledChannelIds,
  }));
});
afterEach(async () => {
  if (root) await act(async () => root.unmount());
  container?.remove();
  vi.unstubAllGlobals();
});

describe('live simulation handoff and persistence', () => {
  it('consumes a Planning request exactly once, saves ID, and clears it on configuration change', async () => {
    const evaluate = vi.fn(async () => response);
    await mount({ available: true, evaluate });
    await act(async () => planning.runEvaluation());
    expect(evaluate).toHaveBeenCalledTimes(1);
    expect(evaluate.mock.calls[0]?.[0]).toEqual(config);
    expect(sim.status).toBe('completed');
    expect(JSON.parse(localStorage.getItem(evaluationSessionKey)!)).toEqual({
      id, selectionKey: 'T+04:CH01,CH02,CH03,CH04,CH05',
    });
    expect(localStorage.getItem(evaluationHandoffKey)).toBeNull();
    await act(async () => planning.setStage('T+02'));
    expect(sim.status).toBe('not_started');
    expect(sim.result).toBeNull();
    expect(localStorage.getItem(evaluationSessionKey)).toBeNull();
  });

  it('restores completed execution from the backend without rerunning it', async () => {
    localStorage.setItem(evaluationSessionKey, JSON.stringify({
      id, selectionKey: 'T+04:CH01,CH02,CH03,CH04,CH05',
    }));
    const evaluate = vi.fn(async () => response);
    const restore = vi.fn(async () => response);
    await mount({ available: true, evaluate, restore });
    expect(restore).toHaveBeenCalledWith(id, expect.any(AbortSignal));
    expect(evaluate).not.toHaveBeenCalled();
    expect(sim.status).toBe('completed');
    expect(sim.result?.id).toBe(id);
  });
  it('distinguishes saved-result verification from agent execution and prevents duplicate starts', async () => {
    localStorage.setItem(evaluationSessionKey, JSON.stringify({
      id, selectionKey: 'T+04:CH01,CH02,CH03,CH04,CH05',
    }));
    let finish!: (value: SimulationResult) => void;
    const evaluate = vi.fn(async () => response);
    const restore = vi.fn(() => new Promise<SimulationResult>(resolve => { finish = resolve; }));
    await mount({ available: true, evaluate, restore });
    expect(sim.status).toBe('restoring');
    expect(sim.result).toBeNull();
    await act(async () => sim.start());
    expect(evaluate).not.toHaveBeenCalled();
    await act(async () => finish(response));
    expect(sim.status).toBe('completed');
    expect(sim.result?.outputs).toEqual(response.outputs);
    expect(JSON.parse(localStorage.getItem(evaluationSessionKey)!).id).toBe(id);
  });

  it('consumes a persisted requested handoff after refresh', async () => {
    localStorage.setItem(evaluationHandoffKey, JSON.stringify({ ...config, status: 'requested' }));
    const evaluate = vi.fn(async () => response);
    await mount({ available: true, evaluate });
    expect(evaluate).toHaveBeenCalledTimes(1);
    expect(sim.status).toBe('completed');
  });

  it('reports failed runs and missing saved results without completed status', async () => {
    const fail = async () => { throw new Error('unavailable'); };
    localStorage.setItem(evaluationSessionKey, JSON.stringify({
      id, selectionKey: 'T+04:CH01,CH02,CH03,CH04,CH05',
    }));
    await mount({ available: true, evaluate: fail, restore: fail });
    expect(sim.status).toBe('error');
    expect(sim.result).toBeNull();
    await act(async () => sim.start());
    expect(sim.status).toBe('error');
    expect(localStorage.getItem(evaluationSessionKey)).toBeNull();
  });

  it('discards an old response when selections change mid-request', async () => {
    let finish!: (value: SimulationResult) => void;
    const evaluate = vi.fn(() => new Promise<SimulationResult>(resolve => { finish = resolve; }));
    await mount({ available: true, evaluate });
    await act(async () => { void sim.start(); });
    expect(sim.status).toBe('running');
    await act(async () => planning.setStage('T+06'));
    await act(async () => finish(response));
    expect(sim.status).toBe('not_started');
    expect(sim.result).toBeNull();
    expect(localStorage.getItem(evaluationSessionKey)).toBeNull();
  });
});

describe('same-origin FastAPI adapter contract', () => {
  it('posts the exact configuration and reads the documented results route', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify(response), { status: 201 }));
    vi.stubGlobal('fetch', fetcher);
    const signal = new AbortController().signal;
    await expect(sadaSimulationAdapter.evaluate(config, signal)).resolves.toEqual(response);
    expect(fetcher).toHaveBeenCalledWith('/api/evaluations', expect.objectContaining({
      method: 'POST', body: JSON.stringify(config), signal,
    }));
    await sadaResultsAdapter.load(id, signal);
    expect(fetcher).toHaveBeenLastCalledWith(`/api/evaluations/${id}`, { signal });
  });

  it('rejects HTML fallbacks, invalid responses, and HTTP failures', async () => {
    const signal = new AbortController().signal;
    for (const value of [
      new Response('<html>frontend</html>'),
      new Response('{}'),
      new Response('{"detail":"unavailable"}', { status: 503 }),
    ]) {
      vi.stubGlobal('fetch', vi.fn(async () => value));
      await expect(sadaSimulationAdapter.evaluate(config, signal)).rejects.toThrow();
    }
  });
});
