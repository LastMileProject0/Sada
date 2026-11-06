import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { ReadinessView } from './readiness';
import { evaluationSchema, metricKeys, groupIds, type EvaluationResult } from '@/lib/results-model';
import { readinessT } from '@/lib/readiness-i18n';
import { evaluationSessionKey } from '@/lib/evaluation-session';

const state = vi.hoisted(() => ({
  language: 'en' as 'en' | 'ar', search: '', navigate: vi.fn(),
}));
vi.mock('wouter', () => ({
  useLocation: () => ['/readiness', state.navigate], useSearch: () => state.search,
}));
vi.mock('@/lib/i18n', () => ({
  useLanguage: () => ({ language: state.language, dir: state.language === 'ar' ? 'rtl' : 'ltr' }),
}));
vi.mock('@/components/shell', () => ({
  Sidebar: () => null, Header: () => null, Panel: () => null, WaveLogo: () => null,
}));

let records: EvaluationResult[], container: HTMLDivElement, root: Root;
beforeAll(() => {
  const path = resolve(process.cwd(), 'tests/readiness-fixtures.py');
  records = JSON.parse(execFileSync('python', [path], { encoding: 'utf8', timeout: 30000 }))
    .map((record: unknown) => evaluationSchema.parse(record));
}, 35000);
beforeEach(() => {
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  state.search = ''; state.language = 'en';
  localStorage.clear();
  container = document.createElement('div'); document.body.append(container);
  root = createRoot(container);
});
afterEach(async () => {
  await act(async () => root.unmount());
  container.remove(); localStorage.clear(); vi.unstubAllGlobals();
});
const element = (id: string) => container.querySelector<HTMLElement>(`[data-testid="${id}"]`);
const text = (id: string) => element(id)?.textContent;
async function render(value: unknown, id?: string, rejected = false) {
  if (id !== undefined) state.search = `?evaluationId=${encodeURIComponent(id)}`;
  const load = vi.fn(async () => {
    if (rejected) throw new Error('private backend diagnostic');
    return value;
  });
  await act(async () => {
    root.render(createElement(ReadinessView, { resultsAdapter: { available: true, load } }));
  });
  return load;
}

describe.each(['en', 'ar'] as const)('Readiness in %s with original engine outputs', language => {
  for (let index = 0; index < 4; index++) {
    it(`renders real stage/channel configuration ${index + 1} without recomputing values`, async () => {
      state.language = language;
      const data = records[index], t = readinessT[language];
      const load = await render(data, data.id);
      expect(load).toHaveBeenCalledOnce();
      expect(text('readiness-stage')).toBe(data.configuration.stage);
      expect(text('readiness-channels')).toContain(data.configuration.enabledChannelIds[0]);
      expect(element('readiness-summary')).not.toBeNull();
      const recommended = data.plans.find(p => p.id === data.recommendedPlanId)!;
      for (const [side, plan] of [['baseline', data.plans[0]], ['recommended', recommended]] as const) {
        for (const key of metricKeys) {
          const metric = plan.metrics[key];
          const expected = !metric ? t.unavailable : metric.unit === 'percent'
            ? `${metric.value.toLocaleString(language, { maximumFractionDigits: 20 })}${t.pct}`
            : `${metric.value.toLocaleString(language)} ${t.residents}`;
          expect(text(`readiness-metric-${key}-${side}`)).toBe(expected);
        }
        expect(text(`readiness-unique-gaps-${side}`)).toBe(t.unavailable);
        for (const group of groupIds) {
          const value = plan.accessibility?.groups.find(g => g.id === group)?.residentsRequiringReview;
          expect(text(`readiness-group-${side}-${group}`)).toBe(value == null ? t.unavailable : `${value.toLocaleString(language)} ${t.residents}`);
        }
        for (const channel of plan.channels) {
          const fields = element(`readiness-channel-${side}-${channel.id}`)!.querySelectorAll('dd');
          const keys = ['selectedAttempts', 'delivered', 'delayed', 'failed', 'unavailable'] as const;
          keys.forEach((key, i) => expect(fields[i].textContent).toBe(
            channel[key] === null ? t.unavailable : channel[key]!.toLocaleString(language),
          ));
        }
      }
      expect(container.textContent).toContain(t.disclaimer);
      expect(container.textContent).toContain(t.stageContext[data.configuration.stage]);
      if (data.recommendedPlanId === 'P0') expect(container.textContent).toContain(t.recIsBaseline);
      expect(document.title).toBe(t.pageTitle);
    });
  }
  it('matches the independently specified T+04 all-five-channel benchmark', () => {
    const data = records[2];
    const p0 = data.plans.find(p => p.id === 'P0')!, p3 = data.plans.find(p => p.id === 'P3')!;
    expect(data.recommendedPlanId).toBe('P3');
    expect([p0.metrics.reach?.value, p3.metrics.reach?.value]).toEqual([722, 942]);
    expect([p0.metrics.effective?.value, p3.metrics.effective?.value]).toEqual([0, 366]);
    expect(p3.metrics.recovery).toEqual({ value: 36.6, unit: 'percent' });
  });
  it('falls back to the saved session selection and preserves it across navigation', async () => {
    state.language = language;
    const data = records[2];
    const saved = JSON.stringify({ id: data.id, selectionKey: 'test-only' });
    localStorage.setItem(evaluationSessionKey, saved);
    await render(data);
    expect(element('readiness-summary')).not.toBeNull();
    for (const path of ['results', 'reports']) {
      await act(async () => element(`link-readiness-${path}`)!.click());
      expect(state.navigate).toHaveBeenLastCalledWith(`/${path}?evaluationId=${encodeURIComponent(data.id)}`);
    }
    expect(localStorage.getItem(evaluationSessionKey)).toBe(saved);
  });
  it('has an honest empty state and a Planning link without calling the adapter', async () => {
    state.language = language;
    const load = await render(records[2]);
    expect(load).not.toHaveBeenCalled();
    expect(element('readiness-empty')).not.toBeNull();
    expect(element('readiness-summary')).toBeNull();
    await act(async () => element('link-readiness-planning')!.click());
    expect(state.navigate).toHaveBeenLastCalledWith('/planning');
  });
  it('does not substitute a recommendation or manufacture missing counts', async () => {
    state.language = language;
    const data = structuredClone(records[2]);
    data.recommendedPlanId = null;
    data.plans[0].metrics.reach = null;
    data.plans[0].channels = [];
    data.plans[0].accessibility = null;
    await render(data, data.id);
    const t = readinessT[language];
    expect(container.textContent).toContain(t.noRec);
    for (const key of metricKeys) expect(text(`readiness-metric-${key}-recommended`)).toBe(t.unavailable);
    expect(text('readiness-metric-reach-baseline')).toBe(t.unavailable);
    expect(text('readiness-unique-gaps-baseline')).toBe(t.unavailable);
    expect(text('readiness-channel-baseline-CH01')).toContain(t.noChannel);
  });
  it('clears previous metrics on unauthorized/error navigation and offers retry', async () => {
    state.language = language;
    await render(records[2], records[2].id);
    expect(element('readiness-summary')).not.toBeNull();
    await render(null, records[0].id, true);
    expect(element('readiness-summary')).toBeNull();
    expect(element('readiness-error')).not.toBeNull();
    expect(element('button-readiness-retry')).not.toBeNull();
    expect(container.textContent).not.toContain('private backend diagnostic');
  });
  it('rejects demo, malformed, and mismatched responses without stale results', async () => {
    state.language = language;
    for (const value of [
      { ...records[2], source: 'verified_demo' },
      { ...records[2], plans: [] },
      { ...records[2], id: 'another-record' },
    ]) {
      await render(value, records[2].id);
      expect(element('readiness-summary')).toBeNull();
      expect(element('readiness-error')).not.toBeNull();
    }
  });
  it('shows loading without metrics for a pending request', async () => {
    state.language = language;
    state.search = `?evaluationId=${records[2].id}`;
    await act(async () => root.render(createElement(ReadinessView, {
      resultsAdapter: { available: true, load: () => new Promise(() => {}) },
    })));
    expect(element('readiness-loading')).not.toBeNull();
    expect(element('readiness-summary')).toBeNull();
  });
});
