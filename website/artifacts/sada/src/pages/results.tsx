import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useSearch } from 'wouter';
import { ArrowLeft, ArrowRight, ShieldCheck, FlaskConical, X, RotateCcw, FileDown, Scale, ChevronRight, ChevronLeft, Database } from 'lucide-react';
import { useLanguage } from '@/lib/i18n';
import { resultsT } from '@/lib/results-i18n';
import { usePlanning } from '@/lib/planning-state';
import { useResults, type ResultsAdapter } from '@/lib/results-state';
import { sadaResultsAdapter } from '@/lib/sada-api-adapters';
import { readSavedEvaluationId } from '@/lib/evaluation-session';
import { evaluationSchema, metricKeys, type EvaluatedPlan } from '@/lib/results-model';
import { downloadEvaluationReport } from '@/lib/results-report';
import { trackEvent } from '@/lib/analytics';
import { Sidebar, Header, Panel, WaveLogo } from '@/components/shell';
import { KpiCard } from '@/components/results/kpi-card';
import { PlanMatrix } from '@/components/results/plan-matrix';
import { AccessibilityPanel } from '@/components/results/accessibility-panel';
import { ChannelPanel } from '@/components/results/channel-panel';
import { RecommendationPanel } from '@/components/results/recommendation-panel';
import '@/components/results/results.css';

export default function Results() {
  return <ResultsView />;
}

/** Adapter injection remains available for isolated tests. */
export function ResultsView({ resultsAdapter = sadaResultsAdapter }: { resultsAdapter?: ResultsAdapter } = {}) {
  const { language, dir } = useLanguage();
  const t = resultsT[language];
  const rtl = dir === 'rtl';
  const { stage, enabledChannels } = usePlanning();
  const search = useSearch();
  const evaluationId = new URLSearchParams(search).get('evaluationId') ?? readSavedEvaluationId();
  const res = useResults(evaluationId, resultsAdapter);
  const { data } = res;
  const [, navigate] = useLocation();
  const [menu, setMenu] = useState(false);
  const [panel, setPanel] = useState<null | 'notifications' | number>(null);
  const [selectedId, setSelectedId] = useState<EvaluatedPlan['id'] | null>(null);
  const [reportError, setReportError] = useState(false);
  const comparison = useRef<HTMLDivElement>(null);
  const canExport = useMemo(() => res.status === 'ready' && evaluationSchema.safeParse(data).success, [data, res.status]);
  const exportReport = () => {
    if (!canExport || !data) return;
    setReportError(false);
    const dimensions = { language, provenance: data.source === 'verified_demo' ? 'demo' as const : 'backend' as const };
    // A request is not confirmation that the browser saved a file.
    trackEvent('report_export_requested', dimensions);
    try {
      downloadEvaluationReport(data, language);
    } catch {
      trackEvent('report_export_failed', dimensions);
      setReportError(true);
    }
  };
  const Back = rtl ? ArrowRight : ArrowLeft;
  const Crumb = rtl ? ChevronLeft : ChevronRight;

  useEffect(() => {
    if (!menu) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMenu(false);
        document.querySelector<HTMLButtonElement>('[data-testid="button-menu"]')?.focus();
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [menu]);

  useEffect(() => {
    const prevTitle = document.title;
    const meta = document.querySelector('meta[name="description"]');
    const prevDesc = meta?.getAttribute('content') ?? null;
    document.title = t.pageTitle;
    meta?.setAttribute('content', t.pageDesc);
    return () => { document.title = prevTitle; if (meta && prevDesc !== null) meta.setAttribute('content', prevDesc); };
  }, [t]);

  useEffect(() => {
    setSelectedId(data ? (data.recommendedPlanId ?? data.plans.find((p) => p.id !== 'P0')?.id ?? data.plans[0].id) : null);
  }, [data]);

  const baseline = useMemo(() => data?.plans.find((p) => p.id === 'P0') ?? null, [data]);
  const selected = useMemo(() => data?.plans.find((p) => p.id === selectedId) ?? null, [data, selectedId]);
  const demo = res.mode === 'demo';
  const scopeStage = data ? data.configuration.stage : stage;
  const scopeChannels = data ? data.configuration.enabledChannelIds : enabledChannels;

  return (
    <div dir="ltr" className="sada-home min-h-[100dvh] bg-background text-foreground">
      <Sidebar active={3} menu={menu} setMenu={setMenu} onNav={(i) => (i === 0 ? navigate('/') : i === 1 ? navigate('/planning') : i === 2 ? navigate('/simulation') : setPanel(i))} />
      <div className="min-w-0 lg:pl-60">
        <Header setMenu={() => setMenu(open => !open)} onNotifications={() => setPanel('notifications')} />
        <main dir={dir} className="relative isolate mx-auto min-w-0 max-w-[1400px] space-y-6 px-4 pb-16 pt-5 md:px-8">
          <nav aria-label="breadcrumb" className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <button data-testid="link-breadcrumb-simulation" onClick={() => navigate('/simulation')} className="hover:text-primary">{t.crumbs[0]}</button>
            <Crumb size={12} /><span aria-current="page" className="text-foreground">{t.crumbs[1]}</span>
          </nav>

          <section className="relative overflow-hidden rounded-3xl border border-white/10">
            <img src={`${import.meta.env.BASE_URL}riyadh-dusk.jpg`} alt="" className="absolute inset-0 h-full w-full object-cover object-[65%_35%] saturate-[1.3]" />
            <div className="absolute inset-0 bg-[linear-gradient(90deg,hsl(229_55%_6%/.95)_0%,hsl(229_55%_6%/.65)_50%,hsl(260_50%_12%/.25)_100%)] rtl:bg-[linear-gradient(270deg,hsl(229_55%_6%/.95)_0%,hsl(229_55%_6%/.65)_50%,hsl(260_50%_12%/.25)_100%)]" />
            <div className="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-background to-transparent" />
            <svg className="pointer-events-none absolute inset-0 h-full w-full opacity-70" viewBox="0 0 1000 300" preserveAspectRatio="none" aria-hidden>
              <path d="M560 260 Q760 40 960 260" stroke="hsl(182 85% 60%/.45)" strokeDasharray="4 6" fill="none" />
              <path d="M620 260 Q760 100 900 260" stroke="hsl(275 80% 66%/.4)" strokeDasharray="4 6" fill="none" />
              {[0, 1, 2].map((i) => <path key={i} className="dash" style={{ animationDuration: `${9 + i * 2}s` }} d={`M0 ${230 + i * 16} C300 ${160 + i * 20} 600 ${280 - i * 10} 1000 ${180 + i * 20}`} stroke={i % 2 ? 'hsl(270 75% 65%/.55)' : 'hsl(182 85% 55%/.55)'} strokeWidth="1" fill="none" />)}
            </svg>
            <div className="relative flex flex-col gap-6 p-6 md:flex-row md:items-end md:justify-between md:p-9">
              <div className="rise max-w-2xl">
                <div className="flex items-center gap-3"><WaveLogo className="h-8 w-16" /><span className="text-[11px] uppercase tracking-[0.24em] text-primary">{t.eyebrow}</span></div>
                <h1 className="mt-3 text-3xl font-bold leading-tight md:text-5xl">{t.title}</h1>
                <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground md:text-[15px]">{t.lede}</p>
                <p className="mt-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[.04] px-3 py-1.5 text-[11px] text-muted-foreground backdrop-blur"><ShieldCheck size={13} className="text-primary" />{t.synthetic}</p>
              </div>
              <div className="rise flex flex-col gap-3 md:items-end" style={{ animationDelay: '120ms' }}>
                <span className="text-[11px] text-muted-foreground">{data ? t.evaluatedScope : t.currentSelection}</span>
                <div dir="ltr" className="flex flex-wrap items-center gap-2 font-mono text-xs">
                  <span className="res-chip text-sm" data-testid="hero-stage">{scopeStage}</span>
                  <span className="res-chip">AL_WADI_FLASH_FLOOD</span>
                </div>
                <div dir="ltr" className="flex flex-wrap gap-1.5" data-testid="hero-channels">{scopeChannels.map((c) => <span key={c} className="res-chip font-mono">{c}</span>)}</div>
                <div className="flex flex-wrap gap-2">
                  <button data-testid="results-back" onClick={() => navigate('/simulation')} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[.04] px-3 py-1.5 text-xs hover:border-primary/50 hover:text-primary"><Back size={13} />{t.back}</button>
                  <button data-testid="button-compare" disabled={!canExport} title={canExport ? t.compareHint : t.compareOff} aria-describedby="compare-off" aria-controls="plan-comparison" onClick={() => {
                    if (!canExport || !data) return;
                    setSelectedId(data.recommendedPlanId ?? 'P0');
                    comparison.current?.scrollIntoView?.({ block: 'start' });
                    comparison.current?.focus({ preventScroll: true });
                  }} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs disabled:opacity-50 enabled:hover:border-primary/50 enabled:hover:text-primary"><Scale size={13} />{t.compare}</button>
                  <button data-testid="button-report" disabled={!canExport} onClick={exportReport} title={canExport ? t.reportHint : t.reportOff} aria-describedby="report-off" className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs disabled:opacity-50 enabled:hover:border-primary/50 enabled:hover:text-primary"><FileDown size={13} />{t.report}</button>
                  <span id="compare-off" className="sr-only">{canExport ? t.compareHint : t.compareOff}</span><span id="report-off" className="sr-only">{canExport ? t.reportHint : t.reportOff}</span>
                </div>
                {reportError && <p role="alert" className="text-xs text-destructive">{t.reportError}</p>}
              </div>
            </div>
          </section>

          {demo ? (
            <div role="status" data-testid="demo-banner" className="res-glass flex flex-col gap-3 rounded-2xl border-[hsl(40_90%_60%/.45)] p-4 sm:flex-row sm:items-center">
              <FlaskConical className="shrink-0 text-[hsl(40_90%_68%)]" size={22} />
              <div className="flex-1"><p className="text-sm font-semibold text-[hsl(40_90%_75%)]">{t.demoBanner}</p><p className="text-xs text-muted-foreground">{t.demoBody}</p></div>
              <button data-testid="results-demo-exit" onClick={() => res.showLive()} className="inline-flex items-center gap-1.5 self-start rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:border-primary/50"><X size={13} />{t.demoExit}</button>
            </div>
          ) : data && <p className="res-chip w-fit" data-testid="badge-live"><Database size={12} />{t.liveBadge}</p>}

          {res.status === 'loading' && (
            <div aria-busy="true" aria-label={t.loading} data-testid="results-loading" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {metricKeys.map((k) => <div key={k} className="res-skel h-40 rounded-2xl" />)}
            </div>
          )}

          {res.status === 'error' && (
            <div role="alert" data-testid="results-error" className="res-glass rounded-2xl p-6">
              <h2 className="text-lg font-semibold">{t.errorTitle}</h2><p className="mt-1 text-sm text-muted-foreground">{t.errorBody}</p>
              <button data-testid="button-retry" onClick={res.retry} className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-primary/20 px-4 py-2 text-sm hover:bg-primary/30"><RotateCcw size={14} />{t.retry}</button>
            </div>
          )}

          {res.status === 'empty' && !data && (
            <section data-testid="results-empty" className="res-glass relative overflow-hidden rounded-3xl p-8 text-center md:p-14">
              <div className="res-scan pointer-events-none absolute inset-x-0 top-0 h-px" />
              <div className="mx-auto grid h-20 w-20 place-items-center rounded-full border border-primary/30 bg-primary/5"><WaveLogo className="h-10 w-16 opacity-80" /></div>
              <h2 className="mt-5 text-2xl font-semibold">{t.emptyTitle}</h2>
              <p className="mx-auto mt-2 max-w-xl text-sm leading-relaxed text-muted-foreground">{t.emptyBody}</p>
              <p className="mx-auto mt-3 max-w-xl text-xs text-muted-foreground/80">{res.integrationPending ? t.pending : !evaluationId ? t.noId : ''}</p>
              <div className="mt-6 flex flex-wrap justify-center gap-3">
                <button data-testid="button-empty-back" onClick={() => navigate('/simulation')} className="inline-flex items-center gap-1.5 rounded-xl bg-primary/20 px-5 py-2.5 text-sm font-medium shadow-[0_0_24px_-8px_hsl(182_90%_55%)] hover:bg-primary/30"><Back size={15} />{t.back}</button>
                <button data-testid="results-demo-toggle" onClick={() => res.showDemo()} className="inline-flex items-center gap-1.5 rounded-xl border border-[hsl(40_90%_60%/.45)] px-5 py-2.5 text-sm text-[hsl(40_90%_75%)] hover:bg-[hsl(40_90%_50%/.08)]"><FlaskConical size={15} />{t.demoShow}</button>
              </div>
            </section>
          )}

          {data && res.status === 'ready' && (
            <>
              <div className="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {metricKeys.map((k, i) => <KpiCard key={k} k={k} index={i} baseline={baseline} plan={selected} t={t} rtl={rtl} />)}
              </div>
              <div id="plan-comparison" ref={comparison} tabIndex={-1} role="region" aria-label={t.compare} className="grid min-w-0 grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
                <PlanMatrix data={data} selectedId={selectedId ?? ''} onSelect={setSelectedId} t={t} />
                <div className="min-w-0 space-y-6">
                  <AccessibilityPanel baseline={baseline} plan={selected} population={data.configuration.population} t={t} />
                  <ChannelPanel key={`${data.id}-${selectedId}`} baseline={baseline} plan={selected} t={t} />
                </div>
              </div>
              <RecommendationPanel data={data} lang={language} t={t} />
            </>
          )}
        </main>
      </div>
      {panel === 'notifications' && <Panel title={t.notifications} onClose={() => setPanel(null)}><p>{t.noNotifications}</p></Panel>}
      {typeof panel === 'number' && <Panel title={t.title} onClose={() => setPanel(null)}><p>{t.soon}</p></Panel>}
    </div>
  );
}
