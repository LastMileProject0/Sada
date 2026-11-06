import type { EvaluationResult } from './results-model';
import { reportPDFContent } from './report-pdf-content';
import { reportFontCSS } from './report-pdf-fonts';
import { paginateReport, PAGE_HEIGHT, PAGE_WIDTH } from './report-pdf-layout';

/** Genuine PDF bytes, generated locally. No API, print dialog, upload or inference. */
export async function createEvaluationPDF(data: EvaluationResult, language: 'en' | 'ar',
  signal = new AbortController().signal) {
  signal.throwIfAborted();
  const report = reportPDFContent(data, language);
  const [fonts, { PDFDocument }, { toPng }] = await Promise.all([
    reportFontCSS(signal), import('pdf-lib'), import('html-to-image'),
  ]);
  const layout = await paginateReport(report.blocks, language, report.title, fonts, signal);
  try {
    const pdf = await PDFDocument.create();
    pdf.setTitle(`${report.title} — SADA`);
    pdf.setAuthor('SADA');
    pdf.setSubject(language === 'ar' ? 'تقييم اصطناعي — ليس شهادة امتثال' : 'Synthetic evaluation — not compliance certification');
    for (const page of layout.pages) {
      signal.throwIfAborted();
      const png = await toPng(page, {
        width: PAGE_WIDTH, height: PAGE_HEIGHT, pixelRatio: 2, backgroundColor: '#ffffff',
        fontEmbedCSS: fonts, skipAutoScale: false,
      });
      signal.throwIfAborted();
      const image = await pdf.embedPng(png);
      pdf.addPage([595.28, 841.89]).drawImage(image, { x: 0, y: 0, width: 595.28, height: 841.89 });
    }
    signal.throwIfAborted();
    const bytes = await pdf.save();
    return { blob: new Blob([new Uint8Array(bytes)], { type: 'application/pdf' }),
      filename: report.filename, pageCount: layout.pages.length };
  } finally {
    layout.dispose();
  }
}

export async function downloadEvaluationPDF(data: EvaluationResult, language: 'en' | 'ar',
  signal: AbortSignal) {
  const report = await createEvaluationPDF(data, language, signal);
  signal.throwIfAborted();
  const url = URL.createObjectURL(report.blob);
  const anchor = document.createElement('a');
  try {
    anchor.href = url; anchor.download = report.filename;
    document.body.append(anchor); anchor.click();
  } finally {
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}
