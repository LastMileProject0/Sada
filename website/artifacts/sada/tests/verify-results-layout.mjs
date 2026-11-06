// Isolated UI/geometry regression: real original-engine aggregates, intercepted
// fixture adapter only. No database, evaluation POST, or AI requests.
import { chromium } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const records = JSON.parse(execFileSync('python', [
  fileURLToPath(new URL('./readiness-fixtures.py', import.meta.url)),
], { encoding: 'utf8' }));
const data = records[2];
const browser = await chromium.launch({ executablePath: '/repl/tools/bin/chromium', headless: true });
let failures = 0;
try {
  for (const language of ['en', 'ar']) {
    const context = await browser.newContext({ reducedMotion: 'reduce' });
    await context.addInitScript(language => localStorage.setItem('sada-language', language), language);
    await context.route('**/__e2e/results/**', route => route.fulfill({ json: data }));
    const page = await context.newPage();
    for (const width of [360, 390, 414]) {
      await page.setViewportSize({ width, height: 844 });
      await page.goto(`http://localhost:80/tests/fixtures/results.html?evaluationId=${data.id}`);
      // Wait for the real four-plan fixture, not the loading/empty KPI shell.
      await page.getByTestId('plan-P3').waitFor();
      const measured = await page.evaluate(() => {
        const width = innerWidth;
        const clipped = [...document.querySelectorAll('main button,main h1,main h2,main h3,main p,main dt,main dd')]
          .filter(el => {
            if (!el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) return false;
            if (el.closest('[role="tooltip"]')) return false;
            if ([...function* (n) { while (n) { yield n; n = n.parentElement; } }(el)]
              .some(n => ['auto', 'scroll'].includes(getComputedStyle(n).overflowX))) return false;
            const r = el.getBoundingClientRect();
            return r.right > width + 1 || r.left < -1;
          }).map(el => el.getAttribute('data-testid') || `${el.tagName}.${el.className}`).slice(0, 8);
        return { viewport: width, document: document.documentElement.scrollWidth, clipped };
      });
      const good = measured.document <= width && !measured.clipped.length;
      if (!good) failures++;
      console.log(language, width, good ? 'PASS' : 'FAIL', JSON.stringify(measured));
    }
    await context.close();
  }
} finally { await browser.close(); }
if (failures) process.exitCode = 1;
