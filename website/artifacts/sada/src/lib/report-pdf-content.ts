import { createEvaluationReport, reportCopy } from './results-report';
import { evaluationSchema, metricKeys, type EvaluationResult } from './results-model';
import { resultsT } from './results-i18n';

export type ReportBlock = { node: HTMLElement; heading?: boolean; table?: number; tableHeader?: HTMLElement };

/** Data enters only as inert, escaped text from the existing validated generator. */
export function reportPDFContent(value: EvaluationResult, language: 'en' | 'ar') {
  const data = evaluationSchema.parse(value);
  if (data.source !== 'backend') throw new Error('PDF requires an authorized backend evaluation');
  const original = createEvaluationReport(data, language);
  const document = new DOMParser().parseFromString(original.html, 'text/html');
  const main = document.querySelector('main')!;
  const c = reportCopy[language], t = resultsT[language];
  const overview = document.createElement('section');
  const heading = document.createElement('h2');
  heading.textContent = t.plansTitle;
  overview.append(heading);
  const comparison = document.createElement('table');
  comparison.className = 'comparison';
  const header = comparison.createTHead().insertRow();
  for (const label of [t.metric, ...data.plans.map(p =>
    `${p.id} — ${t.planNames[p.id]}${p.id === data.recommendedPlanId ? ` (${t.recPlan})` : ''}`)]) {
    const cell = document.createElement('th');
    cell.textContent = label;
    header.append(cell);
  }
  const body = comparison.createTBody();
  for (const key of metricKeys) {
    const row = body.insertRow();
    const label = document.createElement('th');
    label.textContent = t.kpi[key];
    row.append(label);
    for (const plan of data.plans) {
      const cell = row.insertCell();
      const metric = plan.metrics[key];
      cell.textContent = metric
        ? `${metric.value.toLocaleString(language, { maximumFractionDigits: 20 })} ${metric.unit === 'residents' ? t.residents : '%'}`
        : c.missing;
    }
  }
  overview.append(comparison);
  // Existing narrative, limitations, per-plan KPIs/accessibility/channels follow.
  main.insertBefore(overview, main.querySelector('section')?.nextSibling ?? null);
  const blocks: ReportBlock[] = [];
  let table = 0;
  const walk = (node: HTMLElement) => {
    const tag = node.tagName;
    if (tag === 'TABLE') {
      const group = ++table;
      for (const row of Array.from(node.querySelectorAll('tbody > tr'))) {
        const item = document.createElement('table');
        item.className = node.className;
        item.createTBody().append(row.cloneNode(true));
        blocks.push({ node: item, table: group, tableHeader: node.querySelector('thead') ?? undefined });
      }
    } else if (/^H[1-4]$/.test(tag)) {
      blocks.push({ node: node.cloneNode(true) as HTMLElement, heading: true });
    } else if (['P', 'LI'].includes(tag) || node.classList.contains('warning')) {
      const clone = node.cloneNode(true) as HTMLElement;
      if (tag === 'LI') clone.className = 'bullet';
      blocks.push({ node: clone });
    } else {
      for (const child of Array.from(node.children)) walk(child as HTMLElement);
    }
  };
  for (const child of Array.from(main.children)) walk(child as HTMLElement);
  return { blocks, filename: original.filename.replace(/\.html$/, '.pdf'), title: c.title };
}
