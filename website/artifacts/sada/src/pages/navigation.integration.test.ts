import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Home from './home';
import Planning from './planning';
import Simulation from './simulation';
import { evaluationSessionKey } from '@/lib/evaluation-session';

const state = vi.hoisted(() => ({
  language: 'en' as 'en' | 'ar',
  search: '',
  navigate: vi.fn(),
  start: vi.fn(),
  runEvaluation: vi.fn(),
}));
vi.mock('wouter', () => ({
  useLocation: () => ['/', state.navigate],
  useSearch: () => state.search,
}));
vi.mock('@/lib/i18n', async importOriginal => {
  const original = await importOriginal<typeof import('@/lib/i18n')>();
  return {
    ...original,
    useLanguage: () => ({
      language: state.language, dir: state.language === 'ar' ? 'rtl' : 'ltr',
      t: original.translations[state.language], setLanguage: vi.fn(),
    }),
  };
});
vi.mock('@/lib/planning-state', async importOriginal => ({
  ...await importOriginal<typeof import('@/lib/planning-state')>(),
  usePlanning: () => ({
    stage: 'T+04', enabledChannels: ['CH01', 'CH02', 'CH03', 'CH04', 'CH05'],
    setStage: vi.fn(), toggleChannel: vi.fn(), runEvaluation: state.runEvaluation,
  }),
}));
vi.mock('@/lib/simulation-state', () => ({
  useLiveSimulation: () => ({
    status: 'not_started', result: null, integrationPending: false,
    error: null, start: state.start, reset: vi.fn(),
  }),
}));

let root: Root;
let container: HTMLDivElement;
const saved = JSON.stringify({
  id: '00000000-0000-4000-8000-000000000001', selectionKey: 'existing-selection',
});

beforeEach(() => {
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  vi.stubGlobal('fetch', vi.fn());
  localStorage.clear();
  localStorage.setItem(evaluationSessionKey, saved);
  state.navigate.mockReset();
  state.search = '';
  state.start.mockReset();
  state.runEvaluation.mockReset();
  container = document.createElement('div');
  document.body.append(container);
  root = createRoot(container);
});
afterEach(async () => {
  await act(async () => root.unmount());
  container.remove();
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe.each(['en', 'ar'] as const)('Compare Plans navigation in %s', language => {
  for (const [name, Page] of [['Home', Home], ['Planning', Planning], ['Simulation', Simulation]] as const) {
    it(`${name} opens About & Limits without touching the saved evaluation`, async () => {
      state.language = language;
      await act(async () => root.render(createElement(Page)));
      const button = container.querySelector<HTMLButtonElement>('[data-testid="nav-6"]');
      expect(button?.textContent).toBe(language === 'en' ? 'About & Limits' : 'عن صدى وحدوده');
      await act(async () => button!.click());
      expect(state.navigate).toHaveBeenCalledExactlyOnceWith('/about');
      expect(localStorage.getItem(evaluationSessionKey)).toBe(saved);
      expect(state.runEvaluation).not.toHaveBeenCalled();
      expect(state.start).not.toHaveBeenCalled();
      expect(fetch).not.toHaveBeenCalled();
    });
    it(`${name} routes to existing Results without rerunning or clearing the saved evaluation`, async () => {
      state.language = language;
      await act(async () => root.render(createElement(Page)));
      const button = container.querySelector<HTMLButtonElement>('[data-testid="nav-3"]');
      expect(button?.textContent).toBe(language === 'en' ? 'Compare Plans' : 'مقارنة الخطط');
      await act(async () => button!.click());
      expect(state.navigate).toHaveBeenCalledExactlyOnceWith('/results');
      expect(state.runEvaluation).not.toHaveBeenCalled();
      expect(state.start).not.toHaveBeenCalled();
      expect(fetch).not.toHaveBeenCalled();
      expect(localStorage.getItem(evaluationSessionKey)).toBe(saved);
    });
    it(`${name} opens Report Center with the existing saved evaluation`, async () => {
      state.language = language;
      await act(async () => root.render(createElement(Page)));
      const button = container.querySelector<HTMLButtonElement>('[data-testid="nav-5"]');
      expect(button?.textContent).toBe(language === 'en' ? 'Report Center' : 'مركز التقارير');
      await act(async () => button!.click());
      expect(state.navigate).toHaveBeenCalledExactlyOnceWith(
        '/reports?evaluationId=00000000-0000-4000-8000-000000000001',
      );
      expect(state.start).not.toHaveBeenCalled();
      expect(state.runEvaluation).not.toHaveBeenCalled();
      expect(fetch).not.toHaveBeenCalled();
    });
  }
  it('Home comparison feature card opens Results, not the explanatory placeholder', async () => {
    state.language = language;
    await act(async () => root.render(createElement(Home)));
    await act(async () => container.querySelector<HTMLButtonElement>('[data-testid="card-feature-2"]')!.click());
    expect(state.navigate).toHaveBeenCalledExactlyOnceWith('/results');
    expect(container.querySelector('[role="dialog"]')).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
  });
  it('navigation still works with no saved evaluation and does not create one', async () => {
    state.language = language;
    localStorage.clear();
    await act(async () => root.render(createElement(Planning)));
    await act(async () => container.querySelector<HTMLButtonElement>('[data-testid="nav-3"]')!.click());
    expect(state.navigate).toHaveBeenCalledExactlyOnceWith('/results');
    expect(localStorage.getItem(evaluationSessionKey)).toBeNull();
    expect(state.runEvaluation).not.toHaveBeenCalled();
  });
  it('Report Center links carry the explicit ID safely instead of silently substituting a saved ID', async () => {
    state.language = language;
    const explicitId = 'explicit&id=not-another-query';
    state.search = `?evaluationId=${encodeURIComponent(explicitId)}`;
    await act(async () => root.render(createElement(Home)));
    await act(async () => container.querySelector<HTMLButtonElement>('[data-testid="nav-5"]')!.click());
    expect(state.navigate).toHaveBeenCalledExactlyOnceWith(
      `/reports?evaluationId=${encodeURIComponent(explicitId)}`,
    );
    expect(localStorage.getItem(evaluationSessionKey)).toBe(saved);
  });
  it('Readiness navigation preserves an explicit or saved evaluation without running it', async () => {
    state.language = language;
    for (const explicit of [null, 'explicit&id=not-another-query']) {
      state.navigate.mockClear();
      state.search = explicit ? `?evaluationId=${encodeURIComponent(explicit)}` : '';
      await act(async () => root.render(createElement(Home)));
      await act(async () => container.querySelector<HTMLButtonElement>('[data-testid="nav-4"]')!.click());
      expect(state.navigate).toHaveBeenCalledExactlyOnceWith(
        `/readiness?evaluationId=${encodeURIComponent(explicit ?? JSON.parse(saved).id)}`,
      );
    }
    expect(state.runEvaluation).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
  });
  it('Readiness with no saved evaluation routes to its empty state', async () => {
    state.language = language;
    localStorage.clear();
    await act(async () => root.render(createElement(Home)));
    await act(async () => container.querySelector<HTMLButtonElement>('[data-testid="nav-4"]')!.click());
    expect(state.navigate).toHaveBeenCalledExactlyOnceWith('/readiness');
    expect(fetch).not.toHaveBeenCalled();
  });
  it('Report Center navigation without a saved ID opens an honest empty-state route', async () => {
    state.language = language;
    localStorage.clear();
    await act(async () => root.render(createElement(Home)));
    await act(async () => container.querySelector<HTMLButtonElement>('[data-testid="nav-5"]')!.click());
    expect(state.navigate).toHaveBeenCalledExactlyOnceWith('/reports');
    expect(fetch).not.toHaveBeenCalled();
  });
});
