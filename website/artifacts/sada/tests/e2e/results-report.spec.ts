import { readFile } from 'node:fs/promises';
import { expect, test, type Page, type TestInfo } from '@playwright/test';

// Intentionally independent expected strings: using the report generator here
// would allow a localization or provenance regression to change both sides.
const copy = {
  ar: {
    dir: 'rtl',
    title: 'تقرير أدلة التقييم',
    provenance: 'بيانات عرض موثّقة — ليست نتائج تقييم مباشر',
    scopeWarning: 'القيم المؤكدة فقط هي الوصول والتغطية الفعالة للخطتين P0 وP3',
    noAlerts: 'لا تُرسل تنبيهات طوارئ حقيقية',
    noLegal: 'ليست حكمًا قانونيًا أو شهادة امتثال',
    missing: 'غير متاح — لم يقدّمه هذا التقييم',
    notEvaluated: 'لم تُقيَّم ضمن هذه النتائج',
    reportError: 'تعذّر تنزيل التقرير. يرجى المحاولة مجددًا.',
  },
  en: {
    dir: 'ltr',
    title: 'Evaluation evidence report',
    provenance: 'Verified demo fixture — not live evaluation output',
    scopeWarning: 'Only P0 and P3 reach and effective coverage are confirmed.',
    noAlerts: 'No real emergency alerts are sent',
    noLegal: 'not a legal verdict or certification',
    missing: 'Unavailable — not supplied by this evaluation',
    notEvaluated: 'Not evaluated in this result',
    reportError: 'The report could not be downloaded. Please try again.',
  },
} as const;
type Language = keyof typeof copy;

async function downloadReport(page: Page, language: Language, info: TestInfo) {
  const expected = copy[language];
  const other = copy[language === 'ar' ? 'en' : 'ar'];
  const downloadEvent = page.waitForEvent('download');
  await page.getByTestId('button-report').click();
  const download = await downloadEvent;
  expect(download.suggestedFilename()).toBe(`SADA-VERIFIED-DEMO-T04-${language}.html`);
  const path = info.outputPath(download.suggestedFilename());
  // Exercise the actual browser download, not a mocked Blob or anchor click.
  await download.saveAs(path);
  expect(await download.failure()).toBeNull();
  const html = await readFile(path, 'utf8');
  expect(html).toMatch(/^<!doctype html>/i);
  expect(html).toContain(`<html lang="${language}" dir="${expected.dir}">`);
  expect(html).toMatch(/<meta charset="utf-8">/i);
  expect(html).toContain(expected.title);
  expect(html).not.toContain(other.title);
  expect(html).not.toContain(other.provenance);
  expect(html).toContain('verified-demo-all-channel-t04');
  expect(html).not.toMatch(/NaN|Infinity|undefined/);

  // Open the saved bytes in a separate browser document to verify UTF-8,
  // language, visible warnings, and the standalone HTML actually renders.
  const report = await page.context().newPage();
  try {
    await report.route('**/__downloaded-report', route => route.fulfill({
      contentType: 'text/html; charset=utf-8', body: html,
    }));
    await report.goto(new URL('__downloaded-report', page.url()).href);
    await expect(report.locator('html')).toHaveAttribute('lang', language);
    await expect(report.locator('html')).toHaveAttribute('dir', expected.dir);
    await expect(report.getByRole('heading', { level: 1 })).toHaveText(expected.title);
    await expect(report.locator('header .warning')).toContainText(expected.provenance);
    await expect(report.locator('header .warning')).toContainText(expected.scopeWarning);
    await expect(report.locator('header .warning')).toContainText(expected.noAlerts);
    await expect(report.locator('header .warning')).toContainText(expected.noLegal);
    await expect(report.locator('footer.warning')).toContainText(expected.provenance);
    await expect(report.locator('main')).toContainText(expected.missing);
    await expect(report.locator('main')).toContainText(expected.notEvaluated);
    await expect(report.locator('main')).toContainText('T+04');
  } finally {
    await report.close();
  }
}

for (const initialLanguage of ['ar', 'en'] as const) {
  test(`demo report saving failure is recoverable in ${initialLanguage}`, async ({ page }, info) => {
    const downloads: string[] = [];
    page.on('download', download => downloads.push(download.suggestedFilename()));
    await page.addInitScript(language => {
      localStorage.setItem('sada-language', language);
    }, initialLanguage);
    await page.goto('./results');
    await page.getByTestId('results-demo-toggle').click();
    await expect(page.getByTestId('demo-banner')).toBeVisible();
    await expect(page.locator('html')).toHaveAttribute('lang', initialLanguage);
    const button = page.getByTestId('button-report');
    const error = page.getByRole('alert').filter({ hasText: copy[initialLanguage].reportError });
    await expect(button).toBeEnabled();
    await expect(error).toHaveCount(0);

    // Keep the real browser function so retry exercises a genuine download.
    const originalCreateObjectURL = await page.evaluateHandle(() => URL.createObjectURL);
    try {
      await page.evaluate(() => {
        URL.createObjectURL = () => { throw new Error('Forced browser report-saving failure'); };
      });
      await button.click();
      await expect(error).toBeVisible();
      await expect(error).toHaveText(copy[initialLanguage].reportError);
      expect(downloads).toEqual([]);
      await expect(button).toBeEnabled();
    } finally {
      await page.evaluate(original => { URL.createObjectURL = original; }, originalCreateObjectURL);
      await originalCreateObjectURL.dispose();
    }

    // Retry in place: do not reload or switch the demo/language to clear state.
    await downloadReport(page, initialLanguage, info);
    await expect(error).toHaveCount(0);
    await expect(page.getByTestId('demo-banner')).toBeVisible();
    expect(downloads).toEqual([`SADA-VERIFIED-DEMO-T04-${initialLanguage}.html`]);
  });

  test(`real demo download follows current language starting in ${initialLanguage}`, async ({ page }, info) => {
    const downloads: string[] = [];
    page.on('download', download => downloads.push(download.suggestedFilename()));
    await page.addInitScript(language => {
      localStorage.setItem('sada-language', language);
    }, initialLanguage);
    await page.goto('./results');
    const button = page.getByTestId('button-report');
    await expect(page.getByTestId('results-empty')).toBeVisible();
    await expect(button).toBeDisabled();
    expect(downloads).toEqual([]);

    await page.getByTestId('results-demo-toggle').click();
    await expect(page.getByTestId('demo-banner')).toBeVisible();
    await expect(button).toBeEnabled();
    await downloadReport(page, initialLanguage, info);

    const nextLanguage = initialLanguage === 'ar' ? 'en' : 'ar';
    await page.getByTestId(`language-${nextLanguage}`).click();
    await expect(page.locator('html')).toHaveAttribute('lang', nextLanguage);
    await expect(page.getByTestId('demo-banner')).toBeVisible();
    await expect(button).toBeEnabled();
    await downloadReport(page, nextLanguage, info);
    expect(downloads).toHaveLength(2);

    await page.getByTestId('results-demo-exit').click();
    await expect(page.getByTestId('demo-banner')).toHaveCount(0);
    await expect(page.getByTestId('results-empty')).toBeVisible();
    await expect(button).toBeDisabled();
    // Language changes must not re-enable stale demo export after exiting.
    await page.getByTestId(`language-${initialLanguage}`).click();
    await expect(button).toBeDisabled();
    expect(downloads).toHaveLength(2);
  });
}

for (const failure of ['http-error', 'invalid-result'] as const) {
  test(`export stays disabled while loading, after ${failure}, and on retry`, async ({ page }) => {
    const downloads: string[] = [];
    page.on('download', download => downloads.push(download.suggestedFilename()));
    // Hold the request explicitly rather than depending on a slow network/timer.
    const pendingRequest = page.waitForRequest('**/__e2e/results/browser-test');
    let release!: () => void;
    const gate = new Promise<void>(resolve => { release = resolve; });
    await page.route('**/__e2e/results/browser-test', async route => {
      await gate;
      await route.fulfill(failure === 'http-error'
        ? { status: 503, body: 'Test service unavailable' }
        : { status: 200, json: { id: 'browser-test', source: 'backend', plans: [] } });
    });
    await page.goto('./tests/fixtures/results.html?evaluationId=browser-test');
    await pendingRequest;
    await expect(page.getByTestId('results-loading')).toBeVisible();
    await expect(page.getByTestId('button-report')).toBeDisabled();
    await page.getByTestId('language-en').click();
    await expect(page.getByTestId('button-report')).toBeDisabled();
    release();
    await expect(page.getByTestId('results-error')).toBeVisible();
    await expect(page.getByTestId('button-report')).toBeDisabled();

    const retryRequest = page.waitForRequest('**/__e2e/results/browser-test');
    await page.getByTestId('button-retry').click();
    await retryRequest;
    await expect(page.getByTestId('results-error')).toBeVisible();
    await page.getByTestId('language-ar').click();
    await expect(page.getByTestId('button-report')).toBeDisabled();
    expect(downloads).toEqual([]);
  });
}
