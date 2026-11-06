import { CHANNEL_IDS } from './planning-state';
import { evaluationSchema, groupIds, metricKeys, type EvaluationResult } from './results-model';
import { resultsT } from './results-i18n';

type Language = 'en' | 'ar';
const copy = {
  en: {
    title: 'Evaluation evidence report',
    id: 'Evaluation identifier',
    source: 'Data provenance',
    stage: 'Snapshot',
    scenario: 'Scenario',
    channels: 'Enabled channels',
    warning: 'Synthetic pre-event planning only. No real emergency alerts are sent. These results are not a legal verdict or certification.',
    missing: 'Unavailable — not supplied by this evaluation',
    translation: 'Unavailable in the selected language — no translation generated',
    originalEnglish: 'Original source text available in English',
    uniqueGaps: 'Unique residents with accessibility gaps',
    attempts: 'attempts',
    counts: 'Channel outcomes are supplied attempt counts, not unique residents. No totals or missing statistics are calculated.',
    evidence: 'Supplied recommendation evidence',
    legal: 'Legal verdict / certification',
    notEvaluated: 'Not evaluated in this result',
    noInference: 'Only supplied values are reproduced. Missing values are not zero. No statistics, AI explanations or legal conclusions are generated.',
  },
  ar: {
    title: 'تقرير أدلة التقييم',
    id: 'معرّف التقييم',
    source: 'مصدر البيانات',
    stage: 'المرحلة',
    scenario: 'السيناريو',
    channels: 'القنوات المفعّلة',
    warning: 'للتخطيط الاصطناعي قبل الأحداث فقط. لا تُرسل تنبيهات طوارئ حقيقية. هذه النتائج ليست حكمًا قانونيًا أو شهادة امتثال.',
    missing: 'غير متاح — لم يقدّمه هذا التقييم',
    translation: 'غير متاح باللغة المختارة — لم تُولَّد ترجمة',
    originalEnglish: 'النص الأصلي المتاح باللغة الإنجليزية',
    uniqueGaps: 'السكان الفريدون ذوو فجوات إتاحة الوصول',
    attempts: 'محاولة',
    counts: 'نتائج القنوات أعداد محاولات مقدّمة وليست أعداد سكان فريدين. لا تُحسب مجاميع أو إحصاءات مفقودة.',
    evidence: 'أدلة التوصية المقدّمة',
    legal: 'الحكم القانوني / شهادة الامتثال',
    notEvaluated: 'لم تُقيَّم ضمن هذه النتائج',
    noInference: 'تُعرض القيم المقدّمة فقط. القيم المفقودة ليست صفرًا. لا تُولَّد إحصاءات أو تفسيرات ذكاء اصطناعي أو استنتاجات قانونية.',
  },
};

// Shared, reviewed wording for additional local document formats.
export const reportCopy = copy;

/** All data, including service-provided prose and identifiers, is inert HTML text. */
function escape(value: string) {
  return value.replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[char]!);
}

/** Revalidate at the export boundary; never export planner state or inferred results. */
export function createEvaluationReport(value: EvaluationResult, language: Language) {
  const data = evaluationSchema.parse(value);
  const t = resultsT[language];
  const c = copy[language];
  const demo = data.source === 'verified_demo';
  const number = (n: number) => n.toLocaleString(language, { maximumFractionDigits: 20 });
  const count = (n: number | null | undefined, unit: string) =>
    n == null ? c.missing : `${number(n)} ${unit}`;
  const row = (label: string, text: string) =>
    `<tr><th scope="row">${escape(label)}</th><td>${escape(text)}</td></tr>`;
  const table = (rows: string[]) => `<table><tbody>${rows.join('')}</tbody></table>`;
  const channelName = (id: string) => `${id} — ${t.chNames[id]}`;
  const planName = (id: string) => `${id} — ${t.planNames[id]}`;
  const ex = data.explanation;
  type Localized = { en: string | null; ar: string | null };
  const localized = (item: Localized | null) => {
    const text = item?.[language];
    return text?.trim() ? text : item && (item.en?.trim() || item.ar?.trim()) ? c.translation : c.missing;
  };
  // Only the approved backend recommendation/unresolved narratives may use this
  // source-language display. Preserve the supplied string exactly; never translate.
  const evidence = (heading: string, items: (Localized | null)[], allowEnglishSource = false) =>
    `<h3>${escape(heading)}</h3><ul>${(items.length ? items : [null]).map(item => {
      const original = allowEnglishSource && ex?.source === 'backend' && language === 'ar'
        && !item?.ar?.trim() && item?.en?.trim() ? item.en : null;
      return original === null ? `<li>${escape(localized(item))}</li>`
        : `<li><span lang="ar" dir="rtl">${escape(c.originalEnglish)}</span><p lang="en" dir="ltr">${escape(original)}</p></li>`;
    }).join('')}</ul>`;

  const plans = data.plans.map(plan => {
    const metrics = table(metricKeys.map(key => {
      const metric = plan.metrics[key];
      return row(t.kpi[key], metric ? count(metric.value, metric.unit === 'residents' ? t.residents : '%') : c.missing);
    }));
    const accessibility = table([
      row(c.uniqueGaps, count(plan.accessibility?.uniqueResidentsWithGaps, t.residents)),
      ...groupIds.map(id => row(t.groups[id], count(
        plan.accessibility?.groups.find(group => group.id === id)?.residentsRequiringReview, t.residents,
      ))),
    ]);
    const channels = CHANNEL_IDS.map(id => {
      const channel = plan.channels.find(item => item.id === id);
      return `<h4>${escape(channelName(id))}</h4>${table(
        (['selectedAttempts', 'delivered', 'delayed', 'failed', 'unavailable'] as const).map(key =>
          row(t.states[key], count(channel?.[key], c.attempts))),
      )}`;
    }).join('');
    return `<section><h2>${escape(planName(plan.id))}</h2>${metrics}
      <h3>${escape(t.accTitle)}</h3><p>${escape(t.accSub)}</p>${accessibility}
      <h3>${escape(t.chTitle)}</h3><p>${escape(t.chSub)}</p><p>${escape(c.counts)}</p>${channels}</section>`;
  }).join('');

  const provenance = demo ? t.demoBanner : t.sourceBackend;
  const html = `<!doctype html>
<html lang="${language}" dir="${language === 'ar' ? 'rtl' : 'ltr'}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>${escape(c.title)} — SADA</title>
<style>
body{font:16px/1.7 system-ui,sans-serif;color:#14213d;background:#fff;margin:0}
main{max-width:960px;margin:auto;padding:32px}h1,h2,h3{line-height:1.4}h2{color:#173b65}
section{margin-block:32px;border-top:2px solid #dce4ef;padding-top:16px}
table{border-collapse:collapse;width:100%;margin-block:12px;overflow-wrap:anywhere}
th,td{border:1px solid #ccd5e0;padding:9px 12px;text-align:start;vertical-align:top}
th{width:48%;background:#f2f5fa}.warning{border:2px solid #9d6200;background:#fff4d9;padding:16px}
.provenance{font-size:1.2rem;font-weight:700}li,p,td{white-space:pre-wrap;overflow-wrap:anywhere}
@media print{main{padding:0}tr{break-inside:avoid}h2,h3,h4{break-after:avoid}}
</style></head><body><main>
<header><p>صدى | SADA</p><h1>${escape(c.title)}</h1>
<div class="warning"><p class="provenance">${escape(provenance)}</p>
${demo ? `<p>${escape(t.demoBody)}</p>` : ''}<p>${escape(c.warning)}</p></div>
<p>${escape(c.noInference)}</p></header>
<section><h2>${escape(t.evaluatedScope)}</h2>${table([
    row(c.id, data.id),
    row(c.source, provenance),
    row(c.scenario, data.configuration.scenario),
    row(c.stage, data.configuration.stage),
    row(t.population, count(data.configuration.population, t.residents)),
    row(c.channels, data.configuration.enabledChannelIds.map(channelName).join(' · ')),
    row(t.plansTitle, data.plans.map(plan => planName(plan.id)).join(' · ')),
    ...(['P0', 'P1', 'P2', 'P3'] as const).filter(id => !data.plans.some(plan => plan.id === id))
      .map(id => row(planName(id), c.notEvaluated)),
  ])}<p>${escape(t.sirenNote)}</p><p>${escape(t.smsNote)}</p></section>
<section><h2>${escape(t.metric)}</h2>${table(metricKeys.map(key => row(t.kpi[key], t.kpiHelp[key])))}</section>
${plans}
<section><h2>${escape(t.recTitle)}</h2>${table([
    row(t.recPlan, data.recommendedPlanId ? planName(data.recommendedPlanId) : t.noRecommendation),
    row(c.evidence, ex ? (ex.source === 'rag' ? t.sourceRag : t.sourceBackend) : c.missing),
  ])}${!ex ? `<p>${escape(t.explPending)}</p>` : ''}
${evidence(t.why, [ex?.reason ?? null], true)}
${evidence(t.improvements, ex?.improvements ?? [])}
${evidence(t.accConsider, ex?.accessibility ?? [])}
${evidence(t.unresolved, [ex?.unresolved ?? null], true)}
${evidence(t.tradeoffs, ex?.tradeoffs ?? [])}
${evidence(t.limitations, ex?.limitations ?? [])}
${table([row(c.legal, c.missing)])}</section>
<footer class="warning">${escape(provenance)}<p>${escape(c.warning)}</p></footer>
</main></body></html>`;

  // Do not place untrusted evaluation IDs in filenames.
  return {
    html,
    filename: `SADA-${demo ? 'VERIFIED-DEMO' : 'evaluation'}-${data.configuration.stage.replace('+', '')}-${language}.html`,
  };
}

export function downloadEvaluationReport(data: EvaluationResult, language: Language) {
  const report = createEvaluationReport(data, language);
  const url = URL.createObjectURL(new Blob([report.html], { type: 'text/html;charset=utf-8' }));
  const anchor = document.createElement('a');
  try {
    anchor.href = url;
    anchor.download = report.filename;
    document.body.appendChild(anchor);
    anchor.click();
  } finally {
    anchor.remove();
    // Give the browser time to start reading the download before releasing it.
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}
