import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Results from './results';
import { verifiedResultsDemo } from '@/lib/results-demo';

// Exercise the real Results button handler, validation, and analytics wrapper.
// Only surrounding page dependencies and the local download boundary are mocked.
const state = vi.hoisted(() => ({
  language: 'en' as 'en' | 'ar',
  result: {} as Record<string, unknown>,
  download: vi.fn(),
}));
vi.mock('@/lib/i18n', () => ({
  useLanguage: () => ({ language: state.language, dir: state.language === 'ar' ? 'rtl' : 'ltr' }),
}));
vi.mock('@/lib/planning-state', async importOriginal => ({
  ...await importOriginal<typeof import('@/lib/planning-state')>(),
  usePlanning: () => ({ stage: 'T+04', enabledChannels: ['CH01'] }),
}));
vi.mock('@/lib/results-state', () => ({ useResults: () => state.result }));
vi.mock('@/lib/results-report', () => ({ downloadEvaluationReport: state.download }));
vi.mock('wouter', () => ({
  useLocation: () => ['/results', vi.fn()],
  useSearch: () => window.location.search,
}));
vi.mock('@/components/shell', () => ({
  Sidebar: () => null, Header: () => null, Panel: () => null, WaveLogo: () => null,
}));
vi.mock('@/components/results/kpi-card', () => ({ KpiCard: () => null }));
vi.mock('@/components/results/plan-matrix', () => ({ PlanMatrix: () => null }));
vi.mock('@/components/results/accessibility-panel', () => ({ AccessibilityPanel: () => null }));
vi.mock('@/components/results/channel-panel', () => ({ ChannelPanel: () => null }));
vi.mock('@/components/results/recommendation-panel', () => ({ RecommendationPanel: () => null }));

const privateId = 'PRIVATE-EVALUATION-DO-NOT-TRACK';
const rawError = 'PRIVATE-LOCAL-ERROR resident=PRIVATE-RESIDENT';
const trackerDefaults = {
  website: 'test-website',
  url: `/results?evaluationId=${privateId}#PRIVATE-FRAGMENT`,
  referrer: `https://private.example/results/${privateId}?token=PRIVATE-TOKEN`,
  title: 'PRIVATE-REPORT-TITLE',
  hostname: 'PRIVATE-HOST',
  name: 'report_export_saved',
  data: {
    evaluationId: privateId, evidence: 'PRIVATE-EVIDENCE', metrics: { reach: 942 },
    residents: ['PRIVATE-RESIDENT'], error: rawError,
  },
};
type Payload = { website: string; url: string; name: string; data: Record<string, unknown> };
let payloads: Payload[];
let track: ReturnType<typeof vi.fn>;
let root: Root;
let container: HTMLDivElement;

function ready(source: 'verified_demo' | 'backend') {
  const data = structuredClone(verifiedResultsDemo);
  data.id = privateId;
  data.source = source;
  data.explanation = {
    source: 'backend', reason: { en: 'PRIVATE-EVIDENCE', ar: 'PRIVATE-AR-EVIDENCE' },
    improvements: [], accessibility: [], unresolved: null, tradeoffs: [], limitations: [],
  };
  // Runtime-only extra fields must not get spread into analytics either.
  Object.assign(data, { residents: ['PRIVATE-RESIDENT'], error: rawError });
  return { data, status: 'ready', mode: source === 'verified_demo' ? 'demo' : 'live' };
}

async function reportButton() {
  await act(async () => { root.render(createElement(Results)); });
  const button = container.querySelector<HTMLButtonElement>('[data-testid="button-report"]');
  expect(button).not.toBeNull();
  return button!;
}

async function click(button: HTMLButtonElement) {
  await act(async () => { button.click(); });
  // Also drain rejected tracker promises so leaks fail the test runner.
  await new Promise(resolve => setTimeout(resolve, 0));
}

function expectEvents(names: string[], provenance: 'demo' | 'backend') {
  expect(track).toHaveBeenCalledTimes(names.length);
  // Exact whole-payload equality denies all unlisted fields at every level,
  // including URL/referrer metadata, raw errors, report data and success claims.
  expect(payloads).toEqual(names.map(name => ({
    website: 'test-website', url: '/results', name,
    data: { language: state.language, provenance },
  })));
  expect(payloads.every(p => ['report_export_requested', 'report_export_failed'].includes(p.name))).toBe(true);
}

beforeEach(() => {
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  window.history.replaceState(null, '', `/results?evaluationId=${privateId}`);
  vi.spyOn(document, 'referrer', 'get').mockReturnValue(trackerDefaults.referrer);
  state.language = 'en';
  state.result = ready('verified_demo');
  state.download.mockReset();
  payloads = [];
  track = vi.fn(callback => {
    expect(callback).toBeTypeOf('function');
    payloads.push(callback(trackerDefaults));
  });
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

describe.each(['en', 'ar'] as const)('Results export analytics in %s', language => {
  describe.each([
    ['verified_demo', 'demo'],
    ['backend', 'backend'],
  ] as const)('%s provenance', (source, provenance) => {
    beforeEach(() => {
      state.language = language;
      state.result = ready(source);
    });

    it('emits exactly one request per valid attempt, never saved or success', async () => {
      const button = await reportButton();
      expect(button.disabled).toBe(false);
      expectEvents([], provenance);
      await click(button);
      expect(state.download).toHaveBeenCalledTimes(1);
      expectEvents(['report_export_requested'], provenance);
      // A re-render must not re-emit; a separate click is a new request.
      await reportButton();
      expectEvents(['report_export_requested'], provenance);
      await click(button);
      expectEvents(['report_export_requested', 'report_export_requested'], provenance);
    });

    it('emits one failure only after a local export exception, without its contents', async () => {
      state.download.mockImplementationOnce(() => { throw new Error(rawError); });
      const button = await reportButton();
      await click(button);
      expect(state.download).toHaveBeenCalledTimes(1);
      expectEvents(['report_export_requested', 'report_export_failed'], provenance);
      await click(button);
      expectEvents(['report_export_requested', 'report_export_failed', 'report_export_requested'], provenance);
    });
  });
});

it.each([
  ['empty', null], ['loading', null], ['error', null], ['ready', null],
  ['loading', verifiedResultsDemo], ['error', verifiedResultsDemo],
  ['ready', { ...verifiedResultsDemo, id: '' }],
] as const)('emits nothing when export is unavailable (%s, data=%j)', async (status, data) => {
  state.result = { status, data, mode: 'live' };
  const button = await reportButton();
  expect(button.disabled).toBe(true);
  await click(button);
  expect(state.download).not.toHaveBeenCalled();
  expectEvents([], 'demo');
});

it.each(['absent', 'throws', 'rejects'] as const)(
  'does not label tracker failure as export failure when tracker %s',
  async mode => {
    if (mode === 'absent') delete window.umami;
    else track.mockImplementation(callback => {
      payloads.push(callback(trackerDefaults));
      if (mode === 'throws') throw new Error(rawError);
      return Promise.reject(new Error(rawError));
    });
    await click(await reportButton());
    expect(state.download).toHaveBeenCalledTimes(1);
    expect(track).toHaveBeenCalledTimes(mode === 'absent' ? 0 : 1);
    expectEvents(mode === 'absent' ? [] : ['report_export_requested'], 'demo');
  },
);

it.each(['en', 'ar'] as const)('Compare control focuses the existing evaluated matrix in %s', async language => {
  state.language = language;
  await reportButton();
  const compare = container.querySelector<HTMLButtonElement>('[data-testid="button-compare"]')!;
  expect(compare.disabled).toBe(false);
  expect(compare.getAttribute('aria-controls')).toBe('plan-comparison');
  await click(compare);
  expect(document.activeElement?.id).toBe('plan-comparison');
  expect(state.download).not.toHaveBeenCalled();
  expect(track).not.toHaveBeenCalled();
});

it('Compare control cannot operate on an evaluation that has not loaded', async () => {
  state.result = { data: null, status: 'loading', mode: 'live' };
  await reportButton();
  const compare = container.querySelector<HTMLButtonElement>('[data-testid="button-compare"]')!;
  expect(compare.disabled).toBe(true);
  expect(container.querySelector('#plan-comparison')).toBeNull();
});
