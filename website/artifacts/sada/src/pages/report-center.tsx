import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useSearch } from 'wouter';
import { FileDown, RotateCcw, ShieldCheck, ChevronRight, ChevronLeft, BarChart3, Layers } from 'lucide-react';
import { useLanguage } from '@/lib/i18n';
import { reportT } from '@/lib/report-center-i18n';
import { resultsT } from '@/lib/results-i18n';
import { useResults, type ResultsAdapter } from '@/lib/results-state';
import { sadaResultsAdapter } from '@/lib/sada-api-adapters';
import { readSavedEvaluationId } from '@/lib/evaluation-session';
import { evaluationSchema } from '@/lib/results-model';
import { downloadEvaluationReport } from '@/lib/results-report';
import { trackEvent } from '@/lib/analytics';
import { Sidebar, Header, Panel, WaveLogo } from '@/components/shell';
import '@/components/results/results.css';

export default function Reports() {
  return <ReportCenterView />;
}

export function ReportCenterView({ resultsAdapter = sadaResultsAdapter }: { resultsAdapter?: ResultsAdapter } = {}) {
  const { language, dir } = useLanguage();
  const t = reportT[language];
  const rt = resultsT[language];
  const Crumb = dir === 'rtl' ? ChevronLeft : ChevronRight;
  const search = useSearch();
  const evaluationId = new URLSearchParams(search).get('evaluationId') ?? readSavedEvaluationId();
  const res = useResults(evaluationId, resultsAdapter);
  const [, navigate] = useLocation();
  const [menu, setMenu] = useState(false);
  const [panel, setPanel] = useState<null | 'notifications' | number>(null);
  const [exportError, setExportError] = useState(false);
  const [pdfBusy, setPdfBusy] = useState(false);
  const pdfRequest = useRef<AbortController | null>(null);
  useEffect(() => {
    setPdfBusy(false);
    setExportError(false);
    return () => {
      pdfRequest.current?.abort();
      pdfRequest.current = null;
    };
  }, [evaluationId, language]);

  // Only a ready, schema-valid, backend-sourced record matching the requested ID is owned and exportable.
  const data = useMemo(() => {
    if (res.status !== 'ready' || res.mode !== 'live' || !res.data || !evaluationId) return null;
    const parsed = evaluationSchema.safeParse(res.data);
    if (!parsed.success || parsed.data.id !== evaluationId || parsed.data.source !== 'backend') return null;
    return res.data;
  }, [res.status, res.mode, res.data, evaluationId]);
  const invalid = res.status === 'ready' && !data;
  const withId = (path: string) => (evaluationId ? `${path}?evaluationId=${encodeURIComponent(evaluationId)}` : path);

  useEffect(() => {
    const prev = document.title;
    const description = document.querySelector('meta[name="description"]');
    const previousDescription = description?.getAttribute('content') ?? null;
    document.title = t.pageTitle;
    description?.setAttribute('content', t.pageDesc);
    return () => {
      document.title = prev;
      if (description && previousDescription !== null) description.setAttribute('content', previousDescription);
    };
  }, [t]);

  const exportReport = () => {
    if (!data) return;
    setExportError(false);
    const dims = { language, provenance: 'backend' as const };
    trackEvent('report_export_requested', dims);
    try { downloadEvaluationReport(data, language); }
    catch { trackEvent('report_export_failed', dims); setExportError(true); }
  };

  const exportPDF = async () => {
    if (!data || pdfRequest.current) return;
    const controller = new AbortController();
    pdfRequest.current = controller;
    setPdfBusy(true);
    setExportError(false);
    const dims = { language, provenance: 'backend' as const };
    trackEvent('report_export_requested', dims);
    try {
      const { downloadEvaluationPDF } = await import('@/lib/results-report-pdf');
      await downloadEvaluationPDF(data, language, controller.signal);
    } catch {
      if (!controller.signal.aborted) {
        trackEvent('report_export_failed', dims);
        setExportError(true);
      }
    } finally {
      if (pdfRequest.current === controller) {
        pdfRequest.current = null;
        setPdfBusy(false);
      }
    }
  };

  const plan = (id: string | null | undefined) => (id ? `${id} — ${rt.planNames[id]}` : t.unavailable);
  const baseline = data?.plans.some(p => p.id === 'P0') ? 'P0' : null;
  const rows: [string, string, string][] = data ? [
    ['id', t.id, data.id],
    ['provenance', t.provenance, t.backend],
    ['scenario', t.scenario, data.configuration.scenario],
    ['stage', t.stage, data.configuration.stage],
    ['channels', t.channels, data.configuration.enabledChannelIds.join(' · ')],
    ['population', t.population, `${data.configuration.population.toLocaleString(language)} ${rt.residents}`],
    ['timestamp', t.timestamp, t.unavailable],
    ['baseline', t.baseline, plan(baseline)],
    ['recommended', t.recommended, data.recommendedPlanId ? plan(data.recommendedPlanId) : t.unavailable],
    ['plans', t.plans, data.plans.map(p => p.id).join(' · ')],
  ] : [];

  const btn = 'inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[.04] px-3 py-1.5 text-xs hover:border-primary/50 hover:text-primary';

  return (
    <div dir="ltr" className="sada-home min-h-[100dvh] bg-background text-foreground">
      <Sidebar active={5} menu={menu} setMenu={setMenu} onNav={(i) => (i === 0 ? navigate('/') : i === 1 ? navigate('/planning') : i === 2 ? navigate('/simulation') : i === 3 ? navigate(withId('/results')) : setPanel(i))} />
      <div className="lg:pl-60">
        <Header setMenu={() => setMenu(o => !o)} onNotifications={() => setPanel('notifications')} />
        <main dir={dir} className="relative mx-auto max-w-[1100px] space-y-6 px-4 pb-16 pt-5 md:px-8">
          <nav aria-label={t.crumbs.join(' / ')} className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <button data-testid="link-breadcrumb-results" onClick={() => navigate(withId('/results'))} className="hover:text-primary">{t.crumbs[0]}</button>
            <Crumb size={12} /><span aria-current="page" className="text-foreground">{t.crumbs[1]}</span>
          </nav>

          <section className="res-glass relative overflow-hidden rounded-3xl p-6 md:p-9">
            <div className="res-scan pointer-events-none absolute inset-x-0 top-0 h-px" />
            <div className="rise flex items-center gap-3"><WaveLogo className="h-8 w-16" /><span className="text-[11px] uppercase tracking-[0.24em] text-primary">{t.eyebrow}</span></div>
            <h1 className="mt-3 text-3xl font-bold md:text-4xl">{t.title}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">{t.lede}</p>
            <p className="mt-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[.04] px-3 py-1.5 text-[11px] text-muted-foreground"><ShieldCheck size={13} className="text-primary" />{t.synthetic}</p>
            <div className="mt-5 flex flex-wrap gap-2">
              <button data-testid="button-download-pdf" disabled={!data || pdfBusy} onClick={() => void exportPDF()} title={data ? t.pdfHint : t.downloadOff} className="inline-flex items-center gap-1.5 rounded-xl bg-primary/20 px-4 py-2 text-sm font-medium disabled:opacity-50 enabled:hover:bg-primary/30"><FileDown size={15} />{pdfBusy ? t.pdfBusy : t.downloadPDF}</button>
              <button data-testid="button-download-report" disabled={!data} onClick={exportReport} title={data ? t.downloadHint : t.downloadOff} className="inline-flex items-center gap-1.5 rounded-xl bg-primary/20 px-4 py-2 text-sm font-medium disabled:opacity-50 enabled:hover:bg-primary/30"><FileDown size={15} />{t.download}</button>
              <button data-testid="link-results" onClick={() => navigate(withId('/results'))} className={btn}><BarChart3 size={13} />{t.toResults}</button>
              <button data-testid="link-planning" onClick={() => navigate('/planning')} className={btn}><Layers size={13} />{t.toPlanning}</button>
            </div>
            <p className="mt-2 text-xs text-muted-foreground" data-testid="text-download-hint">{data ? t.downloadHint : t.downloadOff}</p>
            {data && <p className="mt-2 text-xs text-muted-foreground">{t.pdfHint}</p>}
            {pdfBusy && <p role="status" aria-live="polite" className="mt-2 text-xs text-primary">{t.pdfBusy}</p>}
            {exportError && <p role="alert" data-testid="report-export-error" className="mt-2 text-xs text-destructive">{t.downloadError}</p>}
          </section>

          {res.status === 'loading' && (
            <div aria-busy="true" aria-label={t.loading} data-testid="report-loading" className="space-y-3">
              {[0, 1, 2, 3].map(i => <div key={i} className="res-skel h-10 rounded-xl" />)}
            </div>
          )}

          {(res.status === 'error' || invalid) && (
            <div role="alert" data-testid="report-error" className="res-glass rounded-2xl p-6">
              <h2 className="text-lg font-semibold">{invalid ? t.unauthorizedTitle : t.errorTitle}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{t.errorBody}</p>
              {res.status === 'error' && <button data-testid="button-retry" onClick={res.retry} className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-primary/20 px-4 py-2 text-sm hover:bg-primary/30"><RotateCcw size={14} />{t.retry}</button>}
            </div>
          )}

          {res.status === 'empty' && (
            <section data-testid="report-empty" className="res-glass rounded-3xl p-8 text-center md:p-12">
              <h2 className="text-xl font-semibold">{t.emptyTitle}</h2>
              <p className="mx-auto mt-2 max-w-lg text-sm text-muted-foreground">{t.emptyBody}</p>
            </section>
          )}

          {data && (
            <section data-testid="report-summary" className="res-glass rounded-2xl p-6">
              <h2 className="mb-4 text-lg font-semibold">{t.summary}</h2>
              <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
                {rows.map(([k, label, value]) => (
                  <div key={k} className="border-b border-white/5 pb-2">
                    <dt className="text-[11px] uppercase tracking-wider text-muted-foreground">{label}</dt>
                    <dd data-testid={`summary-${k}`} dir={['id', 'scenario', 'stage', 'channels', 'plans'].includes(k) ? 'ltr' : undefined} className="mt-0.5 break-all font-mono text-sm">{value}</dd>
                  </div>
                ))}
              </dl>
            </section>
          )}
        </main>
      </div>
      {panel === 'notifications' && <Panel title={t.notifications} onClose={() => setPanel(null)}><p>{t.noNotifications}</p></Panel>}
      {typeof panel === 'number' && <Panel title={t.title} onClose={() => setPanel(null)}><p>{t.soon}</p></Panel>}
    </div>
  );
}
