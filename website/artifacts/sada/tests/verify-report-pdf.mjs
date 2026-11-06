// File-generation integration checks only, using explicitly synthetic fixtures.
// Does not create evaluations, use an owned session, or call any AI endpoint.
import { chromium } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { PDFDocument } from 'pdf-lib';

const out = fileURLToPath(new URL('../../../generated-artifacts/report-pdf/', import.meta.url));
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ executablePath: '/repl/tools/bin/chromium', headless: true });
try {
  const page = await browser.newPage();
  await page.route('**/api/policy/**', route => route.abort());
  await page.goto('http://localhost:80/reports');
  await page.waitForLoadState('networkidle');
  for (const language of ['en', 'ar']) {
    const result = await page.evaluate(async language => {
      const { verifiedResultsDemo } = await import('/src/lib/results-demo.ts');
      const { reportPDFContent } = await import('/src/lib/report-pdf-content.ts');
      const { reportFontCSS } = await import('/src/lib/report-pdf-fonts.ts');
      const { paginateReport } = await import('/src/lib/report-pdf-layout.ts');
      const { createEvaluationPDF } = await import('/src/lib/results-report-pdf.ts');
      // Test-only synthetic data; not an authorized production report or a fake API.
      const data = structuredClone(verifiedResultsDemo);
      data.source = 'backend';
      data.id = '00000000-0000-4000-8000-000000000001';
      // Explicitly synthetic export-only narratives: never insert an evaluation.
      const reason = '  Synthetic supplied recommendation [SYNTHETIC-01].\nPreserve the exact original wording; do not generate an Arabic translation.  ';
      const unresolved = 'Synthetic unresolved cases remain under review. <not-markup> & no legal verdict.';
      data.explanation = {
        source: 'backend', reason: { en: reason, ar: null },
        unresolved: { en: unresolved, ar: null },
        improvements: [], accessibility: [], tradeoffs: [], limitations: [],
      };
      const controller = new AbortController();
      const content = reportPDFContent(data, language);
      const fonts = await reportFontCSS(controller.signal);
      const layout = await paginateReport(content.blocks, language, content.title, fonts, controller.signal);
      let sourceComplete = false, overflow = false;
      try {
        const text = layout.pages.map(p => p.querySelector('.pdf-content').textContent).join('\n');
        sourceComplete = content.blocks.every(b => text.includes(b.node.textContent));
        if (!text.includes(reason) || !text.includes(unresolved)) throw new Error('Supplied narratives lost');
        const sourceBlocks = layout.pages.flatMap(p => [...p.querySelectorAll('p[lang="en"][dir="ltr"]')]);
        if (language === 'ar' && (sourceBlocks.length !== 2
          || !text.includes('النص الأصلي المتاح باللغة الإنجليزية'))) throw new Error('English source label/direction lost');
        if (language === 'en' && sourceBlocks.length !== 0) throw new Error('English export changed to fallback format');
        overflow = layout.pages.some(p => {
          const area = p.querySelector('.pdf-content');
          return area.scrollHeight > area.clientHeight || p.offsetWidth !== 794 || p.offsetHeight !== 1123;
        });
      } finally { layout.dispose(); }
      const generated = await createEvaluationPDF(data, language, controller.signal);
      const bytes = new Uint8Array(await generated.blob.arrayBuffer());
      let binary = '';
      for (let i = 0; i < bytes.length; i += 8192) binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
      return { base64: btoa(binary), filename: generated.filename, pages: generated.pageCount,
        sourceComplete, overflow, leftoverFrames: document.querySelectorAll('iframe').length };
    }, language);
    if (!result.sourceComplete || result.overflow || result.leftoverFrames) {
      throw new Error(`${language}: content/overflow/cleanup verification failed`);
    }
    const bytes = Buffer.from(result.base64, 'base64');
    if (!bytes.subarray(0, 5).equals(Buffer.from('%PDF-'))) throw new Error('Invalid PDF header');
    const parsed = await PDFDocument.load(bytes);
    if (parsed.getPageCount() !== result.pages || !result.pages) throw new Error('Invalid page count');
    for (const p of parsed.getPages()) {
      if (Math.abs(p.getWidth() - 595.28) > 0.01 || Math.abs(p.getHeight() - 841.89) > 0.01) {
        throw new Error('Not A4');
      }
    }
    await writeFile(`${out}/synthetic-${language}.pdf`, bytes);
    console.log(`${language}: PASS; pages=${result.pages}; bytes=${bytes.length}; complete=true; overflow=false; valid A4 PDF; frames cleaned`);
  }
} finally { await browser.close(); }
