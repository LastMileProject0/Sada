import { act, createElement as h } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { Router, Route, Switch } from 'wouter';
import { memoryLocation } from 'wouter/memory-location';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Home from './home';
import Planning from './planning';
import Simulation from './simulation';
import Results from './results';
import { LanguageProvider, languageStorageKey, translations } from '@/lib/i18n';
import { PlanningProvider } from '@/lib/planning-state';
import { evaluationSessionKey, saveEvaluation } from '@/lib/evaluation-session';
import { verifiedResultsDemo } from '@/lib/results-demo';
import { resultsT } from '@/lib/results-i18n';

// Navigation must never start an evaluation. Execution/restoration is covered
// separately; keep it idle here while exercising the real sidebar and Results.
vi.mock('@/lib/simulation-state', () => ({
  useLiveSimulation: () => ({
    status: 'idle', result: null, integrationPending: false, error: null,
    start: vi.fn(), reset: vi.fn(),
  }),
}));

const id = '3e366560-9eab-48e3-a1ad-a00000000001';
let root: Root;
let container: HTMLDivElement;
let request: ReturnType<typeof vi.fn>;

beforeEach(() => {
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  localStorage.clear();
  container = document.createElement('div');
  document.body.append(container);
  root = createRoot(container);
  request = vi.fn();
  vi.stubGlobal('fetch', request);
});

afterEach(async () => {
  await act(async () => root.unmount());
  container.remove();
  localStorage.clear();
  vi.unstubAllGlobals();
});

async function mount(path: string, language: 'en' | 'ar') {
  localStorage.setItem(languageStorageKey, language);
  const location = memoryLocation({ path });
  await act(async () => {
    root.render(h(LanguageProvider, null, h(PlanningProvider, null,
      h(Router, { hook: location.hook }, h(Switch, null,
        h(Route, { path: '/', component: Home }),
        h(Route, { path: '/planning', component: Planning }),
        h(Route, { path: '/simulation', component: Simulation }),
        h(Route, { path: '/results', component: Results }),
      )),
    )));
  });
  return location;
}

async function compare() {
  const button = container.querySelector<HTMLButtonElement>('[data-testid="nav-3"]');
  expect(button).not.toBeNull();
  await act(async () => button!.click());
}

describe.each(['en', 'ar'] as const)('Compare Plans in %s', language => {
  describe.each(['/', '/planning', '/simulation'])('from %s', path => {
    it('opens the saved backend result, retains language, and survives remount', async () => {
      saveEvaluation(id, 'T+04:CH01');
      const result = { ...structuredClone(verifiedResultsDemo), id, source: 'backend' };
      request.mockResolvedValue({ ok: true, json: async () => result });
      await mount(path, language);
      expect(container.querySelector('[data-testid="nav-3"]')?.textContent).toContain(translations[language].nav[3]);
      await compare();
      expect(request).toHaveBeenCalledWith(`/api/evaluations/${id}`, { signal: expect.any(AbortSignal) });
      expect(container.querySelector('[data-testid="badge-live"]')).not.toBeNull();
      expect(container.querySelector('[data-testid="demo-banner"]')).toBeNull();
      expect(container.querySelector('main')?.dir).toBe(language === 'ar' ? 'rtl' : 'ltr');
      expect(document.documentElement.lang).toBe(language);
      expect(container.querySelector('[role="dialog"]')).toBeNull();
      await act(async () => root.unmount());
      root = createRoot(container);
      await mount('/results', language);
      expect(container.querySelector('[data-testid="badge-live"]')).not.toBeNull();
      expect(request).toHaveBeenCalledTimes(2);
      // All calls are reads, never POST/evaluate.
      expect(request.mock.calls.every(([, options]) => !options.method)).toBe(true);
    });

    it('shows the honest empty state when no evaluation is saved', async () => {
      await mount(path, language);
      await compare();
      expect(container.querySelector('[data-testid="results-empty"]')?.textContent).toContain(resultsT[language].noId);
      expect(request).not.toHaveBeenCalled();
      expect(container.querySelector('[data-testid="button-report"]')?.hasAttribute('disabled')).toBe(true);
      expect(container.querySelector('[data-testid="demo-banner"]')).toBeNull();
    });

    it.each([403, 404])('does not show results when ownership is unavailable (%s)', async status => {
      saveEvaluation(id, 'T+04:CH01');
      request.mockResolvedValue({ ok: false, status });
      await mount(path, language);
      await compare();
      expect(container.querySelector('[data-testid="results-error"]')?.textContent).toContain(resultsT[language].errorBody);
      expect(container.querySelector('[data-testid="badge-live"]')).toBeNull();
      expect(container.querySelector('[data-testid="demo-banner"]')).toBeNull();
      expect(container.querySelector('[data-testid="button-report"]')?.hasAttribute('disabled')).toBe(true);
      const retry = container.querySelector<HTMLButtonElement>('[data-testid="button-retry"]')!;
      await act(async () => retry.click());
      expect(request).toHaveBeenCalledTimes(2);
      await act(async () => container.querySelector<HTMLButtonElement>('[data-testid="results-back"]')!.click());
      expect(container.querySelector('[data-testid="nav-2"]')?.getAttribute('aria-current')).toBe('page');
    });
  });
});

it.each(['not-json', JSON.stringify({ id: 'not-a-uuid', selectionKey: '' })])(
  'ignores malformed saved references: %s', async saved => {
    localStorage.setItem(evaluationSessionKey, saved);
    await mount('/', 'en');
    await compare();
    expect(container.querySelector('[data-testid="results-empty"]')).not.toBeNull();
    expect(request).not.toHaveBeenCalled();
  },
);

it('still navigates to the empty Results page when browser storage is blocked', async () => {
  await mount('/', 'en');
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked'); });
  await compare();
  expect(container.querySelector('[data-testid="results-empty"]')).not.toBeNull();
  expect(request).not.toHaveBeenCalled();
});
