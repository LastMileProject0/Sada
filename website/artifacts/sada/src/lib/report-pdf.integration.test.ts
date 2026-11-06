import { describe, expect, it } from 'vitest';
import { reportPDFContent } from './report-pdf-content';
import { verifiedResultsDemo } from './results-demo';
import type { EvaluationResult } from './results-model';
import { createEvaluationReport, reportCopy } from './results-report';

function fixture() {
  const data = structuredClone(verifiedResultsDemo);
  data.source = 'backend';
  return data;
}

describe.each(['en', 'ar'] as const)('PDF source content in %s', language => {
  it('retains exact backend narratives, provenance and inert text in HTML and PDF blocks', () => {
    const data = fixture();
    const reason = '  Supplied reason [SRC-01]\n<em>not markup</em> & original.  ';
    const unresolved = 'Existing unresolved scope — not legal authorization.';
    data.explanation = {
      source: 'backend', reason: { en: reason, ar: null },
      unresolved: { en: unresolved, ar: null },
      improvements: [{ en: 'Outside approved fallback scope', ar: null }],
      accessibility: [], tradeoffs: [], limitations: [],
    };
    const html = new DOMParser().parseFromString(createEvaluationReport(data, language).html, 'text/html');
    const pdf = reportPDFContent(data, language);
    const allText = pdf.blocks.map(b => b.node.textContent).join('\n');
    expect(allText).toContain(reason);
    expect(allText).toContain(unresolved);
    expect(html.querySelector('em')).toBeNull();
    expect(allText).toContain(reportCopy[language].missing);
    if (language === 'ar') {
      expect(html.querySelectorAll('p[lang="en"][dir="ltr"]')).toHaveLength(2);
      expect(allText).toContain(reportCopy.ar.originalEnglish);
      expect(allText).not.toContain('Outside approved fallback scope');
    } else {
      expect(html.querySelectorAll('p[lang="en"]')).toHaveLength(0);
      expect(allText).not.toContain(reportCopy.en.originalEnglish);
    }
  });
  it('prefers supplied Arabic and never relabels RAG output as backend English source', () => {
    const data = fixture();
    data.explanation = {
      source: 'backend', reason: { en: 'Original reason', ar: 'السبب المقدّم' },
      unresolved: { en: ' \n ', ar: null }, improvements: [], accessibility: [], tradeoffs: [], limitations: [],
    };
    let html = createEvaluationReport(data, 'ar').html;
    expect(html).toContain('السبب المقدّم');
    expect(html).not.toContain('Original reason');
    expect(html).not.toContain(reportCopy.ar.originalEnglish);
    data.explanation.source = 'rag';
    data.explanation.reason = { en: 'RAG supplied output', ar: null };
    html = createEvaluationReport(data, 'ar').html;
    expect(html).not.toContain('RAG supplied output');
    expect(html).not.toContain(reportCopy.ar.originalEnglish);
    expect(html).toContain(reportCopy.ar.translation);
  });
  it('preserves every supplied source string and adds only the actual plan comparison', () => {
    const data = fixture();
    const pdf = reportPDFContent(data, language);
    const original = new DOMParser().parseFromString(createEvaluationReport(data, language).html, 'text/html');
    const allText = pdf.blocks.map(b => b.node.textContent).join('\n');
    for (const cell of original.querySelectorAll('td,th,li,p,h1,h2,h3,h4')) {
      if (cell.textContent?.trim()) expect(allText).toContain(cell.textContent);
    }
    expect(pdf.filename).toMatch(new RegExp(`-${language}\\.pdf$`));
    expect(allText).toContain(data.id);
    expect(allText).toContain(reportCopy[language].warning);
    expect(pdf.blocks.some(b => b.node.className === 'comparison')).toBe(true);
  });
  it('keeps hostile prose inert, identifiers out of filenames and missing metrics unavailable', () => {
    const data = fixture();
    data.id = '<script>alert("private")</script>';
    data.plans[0].metrics.reach = null;
    const result = reportPDFContent(data, language);
    expect(result.filename).not.toContain('script');
    expect(result.blocks.map(b => b.node.textContent).join('')).toContain(data.id);
    expect(result.blocks.map(b => b.node.textContent).join('')).toContain(reportCopy[language].missing);
    expect(result.blocks.every(b => !b.node.querySelector('script,img,iframe,a'))).toBe(true);
  });
  it('rejects demo data and malformed evaluations instead of producing a nominal PDF', () => {
    expect(() => reportPDFContent(verifiedResultsDemo, language)).toThrow();
    expect(() => reportPDFContent({ ...fixture(), plans: [] } as EvaluationResult, language)).toThrow();
  });
});
