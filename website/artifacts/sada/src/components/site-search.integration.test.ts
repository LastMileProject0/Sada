import { act, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SiteSearch } from './site-search';

const state = vi.hoisted(() => ({ language: 'en' as 'en' | 'ar', navigate: vi.fn() }));
vi.mock('wouter', () => ({
  useLocation: () => ['/reports', state.navigate],
  useSearch: () => '?evaluationId=owned%26id',
}));
vi.mock('@/lib/i18n', () => ({
  translations: {
    en: { nav: ['Home', 'Planning', 'Testing & Simulation', 'Compare Plans', 'Resilience', 'Report Center'] },
    ar: { nav: ['الرئيسية', 'التخطيط', 'الاختبار والمحاكاة', 'مقارنة الخطط', 'الجاهزية والمرونة', 'مركز التقارير'] },
  },
  useLanguage: () => ({ language: state.language, dir: state.language === 'ar' ? 'rtl' : 'ltr', t: { search: 'Search' } }),
}));
let container: HTMLDivElement, root: ReturnType<typeof createRoot>;
beforeEach(() => {
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  vi.stubGlobal('fetch', vi.fn());
  localStorage.clear();
  container = document.createElement('div'); document.body.append(container); root = createRoot(container);
});
afterEach(async () => {
  await act(async () => root.unmount());
  container.remove(); vi.unstubAllGlobals();
});
async function type(value: string) {
  const field = container.querySelector<HTMLInputElement>('[data-testid="input-search"]')!;
  await act(async () => {
    field.focus();
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(field, value);
    field.dispatchEvent(new Event('input', { bubbles: true }));
  });
  return field;
}
describe.each(['en', 'ar'] as const)('page search in %s', language => {
  it('navigates matched pages and retains the explicit evaluation without requests or storage', async () => {
    state.language = language;
    await act(async () => root.render(createElement(SiteSearch)));
    const field = await type(language === 'ar' ? 'النتائج' : 'results');
    expect(container.querySelector('[data-testid="search-result-results"]')).not.toBeNull();
    await act(async () => field.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true })));
    expect(state.navigate).toHaveBeenCalledWith('/results?evaluationId=owned%26id');
    expect(container.querySelector('[data-testid="search-panel"]')).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
    expect(localStorage.length).toBe(0);
  });
  it('shows an honest no-results state and dismisses with Escape', async () => {
    state.language = language;
    await act(async () => root.render(createElement(SiteSearch)));
    const field = await type('zzz-no-match');
    expect(container.querySelector('[data-testid="search-no-results"]')).not.toBeNull();
    await act(async () => field.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })));
    expect(container.querySelector('[data-testid="search-panel"]')).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
  });
});
