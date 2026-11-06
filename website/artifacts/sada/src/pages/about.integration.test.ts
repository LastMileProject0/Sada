import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import About from './about';
import Planning from './planning';
import { evaluationSessionKey } from '@/lib/evaluation-session';

const state = vi.hoisted(() => ({ language: 'en' as 'en' | 'ar', navigate: vi.fn() }));
vi.mock('wouter', () => ({ useLocation: () => ['/about', state.navigate], useSearch: () => '' }));
vi.mock('@/lib/i18n', async importOriginal => {
  const original = await importOriginal<typeof import('@/lib/i18n')>();
  return { ...original, useLanguage: () => ({
    language: state.language, dir: state.language === 'ar' ? 'rtl' : 'ltr',
    t: original.translations[state.language], setLanguage: vi.fn(),
  }) };
});
vi.mock('@/lib/planning-state', async importOriginal => ({
  ...await importOriginal<typeof import('@/lib/planning-state')>(),
  usePlanning: () => ({ stage: 'T+04', enabledChannels: ['CH01'], setStage: vi.fn(), toggleChannel: vi.fn(), runEvaluation: vi.fn() }),
}));

let container: HTMLDivElement;
let root: Root;
const saved = JSON.stringify({ evaluationId: '00000000-0000-4000-8000-000000000001' });
beforeEach(() => {
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  state.navigate.mockReset();
  vi.stubGlobal('fetch', vi.fn());
  localStorage.setItem(evaluationSessionKey, saved);
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

describe.each(['en', 'ar'] as const)('About & Limits in %s', language => {
  it('renders accurate, semantic content without network calls', async () => {
    state.language = language;
    await act(async () => root.render(createElement(About)));
    const text = container.textContent ?? '';
    expect(container.querySelectorAll('h1')).toHaveLength(1);
    expect(container.querySelectorAll('section h2')).toHaveLength(6);
    expect(container.querySelector('main')?.getAttribute('dir')).toBe(language === 'ar' ? 'rtl' : 'ltr');
    for (const s of ['1,000', 'AL_WADI_FLASH_FLOOD', 'T+00', 'T+06', 'ReviewRequired', 'Qwen']) expect(text).toContain(s);
    for (const id of ['CH01', 'CH02', 'CH03', 'CH04', 'CH05']) expect(container.querySelector(`[data-testid="row-channel-${id}"]`)).not.toBeNull();
    expect(container.querySelectorAll('[data-testid^="card-agent-"]')).toHaveLength(4);
    expect(container.querySelectorAll('[data-testid^="text-limit-"]')).toHaveLength(4);
    expect(text).toContain(language === 'en' ? 'Not UAE-Alert Cell Broadcast' : 'ليست البث الخلوي');
    expect(text).toContain(language === 'en' ? 'No legal certification' : 'لا شهادة قانونية');
    expect(document.title).toContain(language === 'en' ? 'About & Limits' : 'عن صدى وحدوده');
    expect(document.head.querySelector('meta[property="og:title"]')?.getAttribute('content')).toBe(document.title);
    expect(document.head.querySelector('meta[name="description"]')?.getAttribute('content')).toBeTruthy();
    expect(fetch).not.toHaveBeenCalled();
  });
  it('marks sidebar index 6 current and keeps saved evaluations on Compare Plans', async () => {
    state.language = language;
    await act(async () => root.render(createElement(About)));
    const about = container.querySelector('[data-testid="nav-6"]')!;
    expect(about.getAttribute('aria-current')).toBe('page');
    expect(about.textContent).toBe(language === 'en' ? 'About & Limits' : 'عن صدى وحدوده');
    await act(async () => container.querySelector<HTMLButtonElement>('[data-testid="nav-3"]')!.click());
    expect(state.navigate).toHaveBeenCalledExactlyOnceWith('/results');
    expect(localStorage.getItem(evaluationSessionKey)).toBe(saved);
  });
  it('opens /about from another page sidebar without placeholder panels', async () => {
    state.language = language;
    await act(async () => root.render(createElement(Planning)));
    await act(async () => container.querySelector<HTMLButtonElement>('[data-testid="nav-6"]')!.click());
    expect(state.navigate).toHaveBeenCalledExactlyOnceWith('/about');
    expect(container.querySelector('[role="dialog"]')).toBeNull();
    expect(localStorage.getItem(evaluationSessionKey)).toBe(saved);
  });
  it('names landmarks, preserves heading order and marks mixed-language identifiers', async () => {
    state.language = language;
    await act(async () => root.render(createElement(About)));
    expect(container.querySelector('main')?.getAttribute('lang')).toBe(language);
    expect(container.querySelector('nav[aria-label]')).not.toBeNull();
    expect(container.querySelectorAll('main h1')).toHaveLength(1);
    for (const section of container.querySelectorAll('section')) {
      const heading = document.getElementById(section.getAttribute('aria-labelledby')!);
      expect(heading?.tagName).toBe('H2');
    }
    for (const link of container.querySelectorAll<HTMLAnchorElement>('a[href^="#about-"]')) {
      expect(document.getElementById(link.hash.slice(1))).not.toBeNull();
    }
    for (const identifier of ['T+06', 'EV03', 'CH01', 'ReviewRequired', 'Qwen', 'CAP']) {
      const node = Array.from(container.querySelectorAll('bdi')).find(n => n.textContent === identifier);
      expect(node?.getAttribute('lang')).toBe('en');
      expect(node?.getAttribute('dir')).toBe('ltr');
    }
    expect(container.querySelector('[data-testid="text-scenario-id"]')?.getAttribute('lang')).toBe('en');
  });
  it('keeps the closed mobile drawer inert and restores keyboard focus on Escape', async () => {
    state.language = language;
    vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
    await act(async () => root.render(createElement(About)));
    const drawer = container.querySelector('#about-navigation')!;
    const opener = container.querySelector<HTMLButtonElement>('[data-testid="button-menu"]')!;
    expect(drawer.hasAttribute('inert')).toBe(true);
    expect(drawer.getAttribute('aria-hidden')).toBe('true');
    expect(opener.getAttribute('aria-expanded')).toBe('false');
    expect(opener.getAttribute('aria-controls')).toBe(drawer.id);
    opener.focus();
    await act(async () => opener.click());
    expect(drawer.hasAttribute('inert')).toBe(false);
    expect(drawer.getAttribute('role')).toBe('dialog');
    expect(drawer.getAttribute('aria-modal')).toBe('true');
    expect(document.activeElement?.getAttribute('data-testid')).toBe('nav-0');
    await act(async () => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true, cancelable: true })));
    expect(document.activeElement?.getAttribute('data-testid')).toBe('nav-6');
    await act(async () => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true })));
    expect(document.activeElement?.getAttribute('data-testid')).toBe('nav-0');
    await act(async () => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })));
    expect(drawer.hasAttribute('inert')).toBe(true);
    expect(document.activeElement).toBe(opener);
    expect(opener.getAttribute('aria-expanded')).toBe('false');
  });
  it('closes the mobile menu when activating its current About destination', async () => {
    state.language = language;
    vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
    await act(async () => root.render(createElement(About)));
    await act(async () => container.querySelector<HTMLButtonElement>('[data-testid="button-menu"]')!.click());
    await act(async () => container.querySelector<HTMLButtonElement>('[data-testid="nav-6"]')!.click());
    expect(container.querySelector('#about-navigation')?.hasAttribute('inert')).toBe(true);
    expect(state.navigate).not.toHaveBeenCalled();
  });
});
