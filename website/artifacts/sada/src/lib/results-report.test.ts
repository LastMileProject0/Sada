import assert from 'node:assert/strict';
import { test } from 'node:test';
import { verifiedResultsDemo } from './results-demo';
import { createEvaluationReport, downloadEvaluationReport } from './results-report';
import { resultsT } from './results-i18n';

test('demo export preserves verified scope, zero and missing values without invented statistics', () => {
  const { html, filename } = createEvaluationReport(verifiedResultsDemo, 'en');
  assert.match(filename, /VERIFIED-DEMO.*en\.html$/);
  assert.match(html, /lang="en" dir="ltr"/);
  assert.match(html, /Verified demo fixture — not live evaluation output/);
  assert.match(html, /T\+04/);
  assert.match(html, /1,000 residents/);
  for (const n of [722, 0, 942, 366]) assert.ok(html.includes(`${n} residents`));
  assert.match(html, /P1 — Recovery Alternative 1<\/th><td>Not evaluated in this result/);
  assert.match(html, /Recovery Improvement<\/th><td>Unavailable/);
  assert.match(html, /Unresolved Critical Cases<\/th><td>Unavailable/);
  assert.match(html, /Why it was selected<\/h3><ul><li>Unavailable/);
  assert.match(html, /No real emergency alerts/);
  assert.match(html, /not a legal verdict/);
  assert.doesNotMatch(html, /Infinity|NaN|72\.2%|94\.2%|36\.6%/);
  assert.equal(verifiedResultsDemo.plans[0].metrics.effective?.value, 0);
});

test('Arabic report keeps Arabic UI and labels exact supplied English backend narratives', () => {
  const data = structuredClone(verifiedResultsDemo);
  data.source = 'backend';
  data.explanation = {
    source: 'backend', reason: { en: 'English-only evidence', ar: null },
    improvements: [], accessibility: [], unresolved: { en: 'Original unresolved evidence [SRC-01]', ar: null }, tradeoffs: [], limitations: [],
  };
  const { html, filename } = createEvaluationReport(data, 'ar');
  assert.match(filename, /evaluation.*ar\.html$/);
  assert.match(html, /lang="ar" dir="rtl"/);
  assert.ok(html.includes(resultsT.ar.kpi.reach));
  assert.ok(html.includes(resultsT.ar.sourceBackend));
  assert.ok(html.includes(`${(722).toLocaleString('ar', { maximumFractionDigits: 20 })} ساكن`));
  assert.match(html, /النص الأصلي المتاح باللغة الإنجليزية/);
  assert.match(html, /<p lang="en" dir="ltr">English-only evidence<\/p>/);
  assert.match(html, /Original unresolved evidence \[SRC-01\]/);
  assert.match(html, /غير متاح — لم يقدّمه هذا التقييم/);
  assert.doesNotMatch(html, /Estimated Reach|Verified demo/);
});

test('backend report includes all supplied metrics, attempt counts, unique gaps and evidence verbatim', () => {
  const data = structuredClone(verifiedResultsDemo);
  data.source = 'backend';
  data.plans[1].metrics.recovery = { value: 12.34567, unit: 'percent' };
  data.plans[1].metrics.critical = { value: 3, unit: 'residents' };
  data.plans[1].accessibility = {
    uniqueResidentsWithGaps: 12,
    groups: [{ id: 'hearing', residentsRequiringReview: 8 }, { id: 'visual', residentsRequiringReview: 9 }],
  };
  data.plans[1].channels = [{
    id: 'CH01', selectedAttempts: 50, delivered: 40, delayed: 0, failed: 10, unavailable: null,
  }];
  data.explanation = {
    source: 'rag', reason: { en: 'Supplied reason', ar: 'سبب مقدّم' },
    improvements: [{ en: 'Supplied improvement', ar: null }],
    accessibility: [{ en: 'Supplied accessibility', ar: null }],
    unresolved: { en: 'Supplied unresolved', ar: null },
    tradeoffs: [{ en: 'Supplied tradeoff', ar: null }],
    limitations: [{ en: 'Supplied limitation', ar: null }],
  };
  const { html } = createEvaluationReport(data, 'en');
  assert.match(html, /12\.34567 %/);
  assert.match(html, /3 residents/);
  assert.match(html, /Unique residents with accessibility gaps<\/th><td>12 residents/);
  assert.doesNotMatch(html, /17 residents/);
  assert.match(html, /Delivered<\/th><td>40 attempts/);
  assert.match(html, /Delayed<\/th><td>0 attempts/);
  assert.match(html, /Unavailable<\/th><td>Unavailable — not supplied/);
  for (const field of ['reason', 'improvement', 'accessibility', 'unresolved', 'tradeoff', 'limitation']) {
    assert.ok(html.includes(`Supplied ${field}`));
  }
  assert.ok(html.includes(resultsT.en.sourceRag));
  assert.doesNotMatch(html, /Verified demo fixture/);
});

test('null recommendation and partially translated evidence remain explicitly unavailable', () => {
  const data = structuredClone(verifiedResultsDemo);
  data.recommendedPlanId = null;
  data.explanation = {
    source: 'backend', reason: { en: '  ', ar: null }, unresolved: null,
    improvements: [], accessibility: [], tradeoffs: [], limitations: [],
  };
  const { html } = createEvaluationReport(data, 'en');
  assert.ok(html.includes(resultsT.en.noRecommendation));
  assert.match(html, /Why it was selected<\/h3><ul><li>Unavailable/);
});

test('unsafe service text is escaped, filenames are safe, and invalid data cannot export', () => {
  const data = structuredClone(verifiedResultsDemo);
  data.id = '../../<script>alert("id")</script>';
  data.explanation = {
    source: 'backend', reason: { en: '<img src=x onerror="alert(1)"> & evidence', ar: null },
    improvements: [], accessibility: [], unresolved: null, tradeoffs: [], limitations: [],
  };
  const { html, filename } = createEvaluationReport(data, 'en');
  assert.match(html, /&lt;script&gt;/);
  assert.match(html, /&lt;img src=x onerror=&quot;alert\(1\)&quot;&gt; &amp; evidence/);
  assert.doesNotMatch(html, /<script|<img|onerror="|src="http/);
  assert.doesNotMatch(filename, /[<>/]/);
  data.plans = [];
  assert.throws(() => createEvaluationReport(data, 'en'));
});

test('download creates a UTF-8 HTML blob, clicks a download link, removes it and releases the URL', async () => {
  const originalDocument = Object.getOwnPropertyDescriptor(globalThis, 'document');
  const originalCreate = URL.createObjectURL;
  const originalRevoke = URL.revokeObjectURL;
  const originalTimeout = globalThis.setTimeout;
  let blob: Blob | undefined;
  let clicked = false;
  let appended = false;
  let removed = false;
  let revoked = '';
  let release: (() => void) | undefined;
  const anchor = { href: '', download: '', click: () => { clicked = true; }, remove: () => { removed = true; } };
  try {
    Object.defineProperty(globalThis, 'document', { configurable: true, value: {
      createElement: (tag: string) => { assert.equal(tag, 'a'); return anchor; },
      body: { appendChild: () => { appended = true; } },
    } });
    URL.createObjectURL = value => { blob = value as Blob; return 'blob:test-report'; };
    URL.revokeObjectURL = url => { revoked = url; };
    globalThis.setTimeout = ((callback: () => void) => { release = callback; return 1; }) as unknown as typeof setTimeout;
    downloadEvaluationReport(verifiedResultsDemo, 'ar');
    assert.ok(appended && clicked && removed);
    assert.equal(anchor.href, 'blob:test-report');
    assert.match(anchor.download, /VERIFIED-DEMO.*ar\.html/);
    assert.equal(blob?.type, 'text/html;charset=utf-8');
    assert.match(await blob!.text(), /تقرير أدلة التقييم/);
    assert.equal(revoked, '');
    release!();
    assert.equal(revoked, 'blob:test-report');
  } finally {
    if (originalDocument) Object.defineProperty(globalThis, 'document', originalDocument);
    else Reflect.deleteProperty(globalThis, 'document');
    URL.createObjectURL = originalCreate;
    URL.revokeObjectURL = originalRevoke;
    globalThis.setTimeout = originalTimeout;
  }
});
