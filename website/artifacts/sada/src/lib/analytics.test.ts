import assert from 'node:assert/strict';
import { test } from 'node:test';
import { trackEvent } from './analytics.ts';

test('report analytics is safe without a browser or injected tracker', () => {
  assert.doesNotThrow(() => trackEvent('report_export_requested', { language: 'en', provenance: 'demo' }));
  const previous = Object.getOwnPropertyDescriptor(globalThis, 'window');
  try {
    Object.defineProperty(globalThis, 'window', { configurable: true, value: {} });
    assert.doesNotThrow(() => trackEvent('report_export_requested', { language: 'en', provenance: 'demo' }));
  } finally {
    if (previous) Object.defineProperty(globalThis, 'window', previous);
    else Reflect.deleteProperty(globalThis, 'window');
  }
});

test('report events send only language and provenance, never extra report fields', () => {
  const previous = Object.getOwnPropertyDescriptor(globalThis, 'window');
  const calls: unknown[] = [];
  try {
    Object.defineProperty(globalThis, 'window', {
      configurable: true,
      value: { umami: { track: (payload: (defaults: object) => unknown) => {
        calls.push(payload({
          website: 'tracker-id',
          url: '/results?evaluationId=private-id',
          referrer: '/results?evaluationId=another-private-id',
          title: 'private report title',
          data: { evidence: 'private evidence' },
        }));
      } } },
    });
    for (const language of ['en', 'ar'] as const) {
      for (const provenance of ['demo', 'backend'] as const) {
        for (const event of ['report_export_requested', 'report_export_failed'] as const) {
          const dimensions = { language, provenance, evaluationId: 'private-id', evidence: 'private-evidence', metrics: 123, residents: ['private'] };
          trackEvent(event, dimensions);
          assert.deepEqual(calls.at(-1), {
            website: 'tracker-id',
            url: '/results',
            name: event,
            data: { language, provenance },
          });
        }
      }
    }
    assert.equal(calls.length, 8);
  } finally {
    if (previous) Object.defineProperty(globalThis, 'window', previous);
    else Reflect.deleteProperty(globalThis, 'window');
  }
});

test('synchronous and asynchronous tracker failures do not interrupt the caller', async () => {
  const previous = Object.getOwnPropertyDescriptor(globalThis, 'window');
  try {
    for (const track of [
      () => { throw new Error('Tracker unavailable'); },
      () => Promise.reject(new Error('Network unavailable')),
    ]) {
      Object.defineProperty(globalThis, 'window', { configurable: true, value: { umami: { track } } });
      let downloadRequested = false;
      assert.doesNotThrow(() => {
        trackEvent('report_export_requested', { language: 'ar', provenance: 'backend' });
        downloadRequested = true;
        trackEvent('report_export_failed', { language: 'ar', provenance: 'backend' });
      });
      assert.equal(downloadRequested, true);
      await new Promise(resolve => setTimeout(resolve, 0));
    }
  } finally {
    if (previous) Object.defineProperty(globalThis, 'window', previous);
    else Reflect.deleteProperty(globalThis, 'window');
  }
});
