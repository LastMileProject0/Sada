import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Reports from './report-center';
import { verifiedResultsDemo } from '@/lib/results-demo';
import { evaluationSessionKey } from '@/lib/evaluation-session';

const state = vi.hoisted(() => ({
  language: 'en' as 'en' | 'ar',
  result: {} as Record<string, unknown>,
  download: vi.fn(),
  pdf: vi.fn(),
  useResults: vi.fn(),
  navigate: vi.fn(),
}));
vi.mock('@/lib/results-report-pdf', () => ({ downloadEvaluationPDF: state.pdf }));
vi.mock('@/lib/i18n', () => ({
  useLanguage: () => ({ language: state.language, dir: state.language === 'ar' ? 'rtl' : 'ltr' }),
}));
vi.mock('@/lib/results-state', () => ({ useResults: state.useResults }));
vi.mock('@/lib/sada-api-adapters', () => ({ sadaResultsAdapter: { available: true, load: vi.fn() } }));
vi.mock('@/lib/results-report', () => ({ downloadEvaluationReport: state.download }));
vi.mock('wouter', () => ({
  useLocation: () => ['/reports', state.navigate],
  useSearch: () => window.location.search,
}));
vi.mock('@/components/shell', () => ({
  Sidebar: () => null, Header: () => null, Panel: () => null, WaveLogo: () => null,
}));

const id = '0b5c8f5e-6c1d-4a8e-9a77-3f2b1d4c5e6f';
const savedId = '9a1f2e3d-4c5b-4a69-8877-665544332211';
let root: Root;
let container: HTMLDivElement;
let track: ReturnType<typeof vi.fn>;

function backend(over: Record<string, unknown> = {}) {
  const data = structuredClone(verifiedResultsDemo);
  data.id = id;
  data.source = 'backend';
  return { data: { ...data, ...over }, status: 'ready', mode: 'live', retry: vi.fn() };
}
async function render() {
  await act(async () => { root.render(createElement(Reports)); });
}

describe.each(['en', 'ar'] as const)('PDF download in %s', language => {
  it('uses only the same validated owned result and selected language', async () => {
    state.language = language;
    state.pdf.mockResolvedValue(undefined);
    await render();
    const button = container.querySelector<HTMLButtonElement>('[data-testid="button-download-pdf"]')!;
    expect(button.disabled).toBe(false);
    await act(async () => { button.click(); });
    expect(state.pdf).toHaveBeenCalledWith(state.result.data, language, expect.any(AbortSignal));
    expect(state.download).not.toHaveBeenCalled();
  });
  it('keeps HTML available and shows a recoverable error if PDF generation fails', async () => {
    state.language = language;
    state.pdf.mockRejectedValue(new Error('private renderer error'));
    await render();
    await act(async () => container.querySelector<HTMLButtonElement>('[data-testid="button-download-pdf"]')!.click());
    expect(container.querySelector('[data-testid="report-export-error"]')).not.toBeNull();
    expect(container.textContent).not.toContain('private renderer error');
    expect(container.querySelector<HTMLButtonElement>('[data-testid="button-download-report"]')!.disabled).toBe(false);
  });
  it('does not export missing, loading or unauthorized data', async () => {
    state.language = language;
    for (const status of ['empty', 'loading', 'error']) {
      state.result = { data: null, status, mode: 'live' };
      await render();
      expect(container.querySelector<HTMLButtonElement>('[data-testid="button-download-pdf"]')!.disabled).toBe(true);
    }
  });
  it('prevents duplicate generation and cancels an in-flight PDF on language change', async () => {
    state.language = language;
    let finish!: () => void;
    state.pdf.mockImplementation(() => new Promise<void>(resolve => { finish = resolve; }));
    await render();
    const button = container.querySelector<HTMLButtonElement>('[data-testid="button-download-pdf"]')!;
    await act(async () => { button.click(); button.click(); });
    expect(state.pdf).toHaveBeenCalledTimes(1);
    expect(button.disabled).toBe(true);
    const signal = state.pdf.mock.calls[0][2] as AbortSignal;
    state.language = language === 'en' ? 'ar' : 'en';
    await render();
    expect(signal.aborted).toBe(true);
    await act(async () => finish());
    expect(container.querySelector<HTMLButtonElement>('[data-testid="button-download-pdf"]')!.disabled).toBe(false);
  });
});
const q = (t: string) => container.querySelector<HTMLElement>(`[data-testid="${t}"]`);
const button = () => q('button-download-report') as HTMLButtonElement;

beforeEach(() => {
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  window.history.replaceState(null, '', `/reports?evaluationId=${id}`);
  localStorage.clear();
  state.language = 'en';
  state.result = backend();
  state.download.mockReset();
  state.navigate.mockReset();
  state.useResults.mockReset().mockImplementation(() => state.result);
  track = vi.fn(cb => cb({ website: 'w' }));
  window.umami = { track };
  container = document.createElement('div');
  document.body.append(container);
  root = createRoot(container);
});
afterEach(async () => {
  await act(async () => { root.unmount(); });
  container.remove();
  delete window.umami;
  vi.unstubAllGlobals();
});

describe.each(['en', 'ar'] as const)('Report Center in %s', language => {
  beforeEach(() => { state.language = language; });

  it('shows the owned summary and exports with exact arguments', async () => {
    await render();
    expect(q('report-summary')).not.toBeNull();
    expect(q('summary-id')?.textContent).toBe(id);
    expect(q('summary-timestamp')?.textContent).toBe(language === 'en' ? 'Unavailable' : 'غير متاح');
    expect(button().disabled).toBe(false);
    await act(async () => { button().click(); });
    expect(state.download).toHaveBeenCalledTimes(1);
    expect(state.download).toHaveBeenCalledWith(state.result.data, language);
    expect(track).toHaveBeenCalledTimes(1);
    expect(track.mock.results[0].value).toEqual({
      website: 'w', url: '/results', name: 'report_export_requested', data: { language, provenance: 'backend' },
    });
  });

  it('reports a local export failure without stale success', async () => {
    state.download.mockImplementationOnce(() => { throw new Error('x'); });
    await render();
    await act(async () => { button().click(); });
    expect(q('report-export-error')).not.toBeNull();
  });

  it.each([
    ['loading', { data: null, status: 'loading', mode: 'live' }, 'report-loading'],
    ['error', { data: null, status: 'error', mode: 'live', retry: vi.fn() }, 'report-error'],
    ['empty', { data: null, status: 'empty', mode: 'live' }, 'report-empty'],
    ['demo provenance', { ...backend({ source: 'verified_demo' }) }, 'report-error'],
    ['demo mode', { ...backend(), mode: 'demo' }, 'report-error'],
    ['mismatched id', backend({ id: 'other-id' }), 'report-error'],
    ['invalid schema', backend({ plans: [] }), 'report-error'],
    ['stale data while loading', { ...backend(), status: 'loading' }, 'report-loading'],
  ] as const)('blocks summary and download when %s', async (_, result, testId) => {
    state.result = result as Record<string, unknown>;
    await render();
    expect(q(testId)).not.toBeNull();
    expect(q('report-summary')).toBeNull();
    expect(button().disabled).toBe(true);
    await act(async () => { button().click(); });
    expect(state.download).not.toHaveBeenCalled();
    expect(track).not.toHaveBeenCalled();
  });
});

describe('evaluation ID resolution', () => {
  it('prefers the explicit query ID over the saved one', async () => {
    localStorage.setItem(evaluationSessionKey, JSON.stringify({ id: savedId, selectionKey: 'k' }));
    await render();
    expect(state.useResults.mock.calls[0][0]).toBe(id);
    await act(async () => { q('link-results')!.click(); });
    expect(state.navigate).toHaveBeenCalledWith(`/results?evaluationId=${id}`);
  });

  it('falls back to the saved session ID', async () => {
    window.history.replaceState(null, '', '/reports');
    localStorage.setItem(evaluationSessionKey, JSON.stringify({ id: savedId, selectionKey: 'k' }));
    state.result = { data: null, status: 'loading', mode: 'live' };
    await render();
    expect(state.useResults.mock.calls[0][0]).toBe(savedId);
  });

  it('uses no ID when none exists and links to Planning', async () => {
    window.history.replaceState(null, '', '/reports');
    state.result = { data: null, status: 'empty', mode: 'live' };
    await render();
    expect(state.useResults.mock.calls[0][0]).toBeNull();
    await act(async () => { q('link-planning')!.click(); });
    expect(state.navigate).toHaveBeenCalledWith('/planning');
  });
});
