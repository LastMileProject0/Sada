import { act, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import { describe, expect, it, vi } from 'vitest';
import { AgentWorkflow } from './agent-workflow';
import { ExecutionControl } from './execution-control';
import { OutputPanels } from './output-panels';
import { simulationT } from '@/lib/simulation-i18n';
import type { ExecutionStatus } from '@/lib/simulation';

vi.mock('./policy-assistant', () => ({ PolicyAssistant: () => null }));

describe.each(['en', 'ar'] as const)('truthful %s lifecycle labels', language => {
  for (const status of ['not_started', 'restoring', 'running', 'completed', 'error'] as ExecutionStatus[]) {
    it(`keeps workflow, control and output labels consistent for ${status}`, async () => {
      vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
      const container = document.createElement('div'); document.body.append(container);
      const root = createRoot(container), t = simulationT[language];
      try {
        await act(async () => root.render(createElement('div', null,
          createElement(AgentWorkflow, { t, status, focused: 0, setFocused: vi.fn(), channels: ['CH01'] }),
          createElement(ExecutionControl, {
            t, status, pending: false, error: status === 'error' ? 'simulation_error' : null,
            resultId: status === 'completed' ? 'owned-evaluation' : null,
            onStart: vi.fn(), onReset: vi.fn(), onBack: vi.fn(), onResults: vi.fn(), rtl: language === 'ar',
          }),
          createElement(OutputPanels, { t, status, outputs: null }),
        )));
        expect(container.querySelector('[data-testid="workflow-status"]')!.textContent).toBe(t.statuses[status]);
        expect(container.querySelector('[data-testid="simulation-status"]')!.textContent).toBe(t.statuses[status]);
        expect(container.textContent).not.toContain(t.unassessed);
        expect(container.querySelector<HTMLButtonElement>('[data-testid="simulation-start"]')!.disabled)
          .toBe(status === 'running' || status === 'restoring');
        if (status === 'completed') {
          expect(container.textContent).not.toContain(t.awaiting);
          expect(container.textContent).not.toContain(t.notRunning);
          expect(container.querySelector('[data-testid="output-policy-state"]')!.textContent).toBe(t.noOutput);
        }
      } finally {
        await act(async () => root.unmount()); container.remove(); vi.unstubAllGlobals();
      }
    });
  }
});
