import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { useLocation, useSearch } from 'wouter';
import { RotateCcw, ShieldCheck, ChevronRight, ChevronLeft, BarChart3, Layers, FileText, Radio, Users, Info } from 'lucide-react';
import { useLanguage } from '@/lib/i18n';
import { readinessT, type ReadinessT } from '@/lib/readiness-i18n';
import { resultsT, type ResultsT } from '@/lib/results-i18n';
import { useResults, type ResultsAdapter } from '@/lib/results-state';
import { sadaResultsAdapter } from '@/lib/sada-api-adapters';
import { readSavedEvaluationId } from '@/lib/evaluation-session';
import { authorizedReadinessEvaluation, readinessPlans } from '@/lib/readiness-model';
import { metricKeys, groupIds, type EvaluatedPlan, type ResultMetric } from '@/lib/results-model';
import { Sidebar, Header, Panel, WaveLogo } from '@/components/shell';
import '@/components/results/results.css';

const CHS = ['CH01', 'CH02', 'CH03', 'CH04', 'CH05'] as const;
const STATES = ['selectedAttempts', 'delivered', 'delayed', 'failed', 'unavailable'] as const;
type Side = 'baseline' | 'recommended';

export default function Readiness() {
  return <ReadinessView />;
}

function setMeta(attr: 'name' | 'property', key: string, value: string) {
  let el = document.head.querySelector<HTMLMetaElement>(`meta[${attr}="${key}"]`);
  const created = !el;
  const prev = el?.getAttribute('content') ?? null;
  if (!el) { el = document.createElement('meta'); el.setAttribute(attr, key); document.head.appendChild(el); }
  el.setAttribute('content', value);
  return () => { if (created) el!.remove(); else if (prev !== null) el!.setAttribute('content', prev); else el!.removeAttribute('content'); };
}

export function ReadinessView({ resultsAdapter = sadaResultsAdapter }: { resultsAdapter?: ResultsAdapter } = {}) {
  const { language, dir } = useLanguage();
  const t = readinessT[language];
  const rt = resultsT[language];
  const Crumb = dir === 'rtl' ? ChevronLeft : ChevronRight;
  const search = useSearch();
  const evaluationId = new URLSearchParams(search).get('evaluationId') ?? readSavedEvaluationId();
  const res = useResults(evaluationId, resultsAdapter);
  const [, navigate] = useLocation();
  const [menu, setMenu] = useState(false);
  const [panel, setPanel] = useState<null | 'notifications' | number>(null);

  const data = useMemo(
    () => (res.status === 'ready' && res.mode === 'live' ? authorizedReadinessEvaluation(res.data, evaluationId) : null),
    [res.status, res.mode, res.data, evaluationId],
  );
  const plans = useMemo(() => (data ? readinessPlans(data) : null), [data]);
  const invalid = res.status === 'ready' && !data;
  const withId = (path: string) => (evaluationId ? `${path}?evaluationId=${encodeURIComponent(evaluationId)}` : path);

  useEffect(() => {
    const prev = document.title;
    document.title = t.pageTitle;
    const undo = [
      setMeta('name', 'description', t.pageDesc),
      setMeta('property', 'og:title', t.pageTitle),
      setMeta('property', 'og:description', t.pageDesc),
      setMeta('property', 'og:type', 'website'),
    ];
    return () => { document.title = prev; undo.forEach(f => f()); };
  }, [t]);

  useEffect(() => {
    if (!menu) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setMenu(false); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [menu]);

  const btn = 'inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[.04] px-3 py-1.5 text-xs hover:border-primary/50 hover:text-primary';
  const planLink = (
    <button data-testid="link-readiness-planning" aria-label={t.toPlanningLabel} onClick={() => navigate('/planning')} className="inline-flex items-center gap-1.5 rounded-xl bg-primary/20 px-4 py-2 text-sm font-medium hover:bg-primary/30"><Layers size={14} />{t.toPlanning}</button>
  );

  return (
    <div dir="ltr" className="sada-home min-h-[100dvh] bg-background text-foreground">
      <Sidebar active={4} menu={menu} setMenu={setMenu} onNav={(i) => (i === 0 ? navigate('/') : i === 1 ? navigate('/planning') : i === 2 ? navigate('/simulation') : i === 3 ? navigate(withId('/results')) : setPanel(i))} />
      <div className="min-w-0 lg:pl-60">
        <Header setMenu={() => setMenu(o => !o)} onNotifications={() => setPanel('notifications')} />
        <main dir={dir} className="rd-main relative mx-auto min-w-0 max-w-[1280px] space-y-6 px-4 pb-16 pt-5 md:px-8">
          <nav aria-label={t.crumbs.join(' / ')} className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
            <button onClick={() => navigate(withId('/results'))} className="hover:text-primary">{t.crumbs[0]}</button>
            <Crumb size={12} /><span aria-current="page" className="text-foreground">{t.crumbs[1]}</span>
          </nav>

          <section className="res-glass relative overflow-hidden rounded-3xl p-5 md:p-9">
            <div className="res-scan pointer-events-none absolute inset-x-0 top-0 h-px" />
            <svg className="rd-rings pointer-events-none absolute -top-24 end-[-6rem] h-80 w-80 opacity-40" viewBox="0 0 200 200" aria-hidden>
              {[30, 55, 80].map((r, i) => <circle key={r} cx="100" cy="100" r={r} fill="none" stroke={i % 2 ? 'hsl(275 80% 66%/.5)' : 'hsl(182 85% 55%/.5)'} strokeDasharray="3 7" />)}
            </svg>
            <div className="relative grid min-w-0 gap-6 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
              <div className="rise min-w-0">
                <div className="flex items-center gap-3"><WaveLogo className="h-8 w-16" /><span className="text-[11px] uppercase tracking-[0.24em] text-primary">{t.eyebrow}</span></div>
                <h1 className="mt-3 text-3xl font-bold leading-tight md:text-5xl">{t.title}</h1>
                <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground md:text-[15px]">{t.lede}</p>
                <p className="mt-4 flex max-w-2xl items-start gap-2 rounded-xl border border-white/10 bg-white/[.04] px-3 py-2 text-[11px] leading-relaxed text-muted-foreground"><ShieldCheck size={14} className="mt-px shrink-0 text-primary" />{t.disclaimer}</p>
              </div>
              <div className="rise flex flex-wrap gap-2 md:flex-col md:items-stretch" style={{ animationDelay: '120ms' }}>
                <button data-testid="link-readiness-results" aria-label={t.toResultsLabel} onClick={() => navigate(withId('/results'))} className={btn}><BarChart3 size={13} />{t.toResults}</button>
                <button data-testid="link-readiness-reports" aria-label={t.toReportsLabel} onClick={() => navigate(withId('/reports'))} className={btn}><FileText size={13} />{t.toReports}</button>
              </div>
            </div>
          </section>

          {res.status === 'loading' && (
            <div aria-busy="true" aria-label={t.loading} data-testid="readiness-loading" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {[0, 1, 2, 3].map(i => <div key={i} className="res-skel h-36 rounded-2xl" />)}
            </div>
          )}

          {(res.status === 'error' || invalid) && (
            <section role="alert" data-testid="readiness-error" className="res-glass rounded-2xl p-6">
              <h2 className="text-lg font-semibold">{invalid ? t.invalidTitle : t.errorTitle}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{invalid ? t.invalidBody : t.errorBody}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {res.status === 'error' && <button data-testid="button-readiness-retry" aria-label={t.retryLabel} onClick={res.retry} className="inline-flex items-center gap-1.5 rounded-xl border border-white/15 px-4 py-2 text-sm hover:border-primary/50"><RotateCcw size={14} />{t.retry}</button>}
                {planLink}
              </div>
            </section>
          )}

          {res.status === 'empty' && (
            <section data-testid="readiness-empty" className="res-glass relative overflow-hidden rounded-3xl p-8 text-center md:p-12">
              <div className="mx-auto grid h-20 w-20 place-items-center rounded-full border border-primary/30 bg-primary/5"><WaveLogo className="h-10 w-16 opacity-80" /></div>
              <h2 className="mt-5 text-xl font-semibold">{t.emptyTitle}</h2>
              <p className="mx-auto mt-2 max-w-lg text-sm text-muted-foreground">{t.emptyBody}</p>
              <div className="mt-6 flex justify-center">{planLink}</div>
            </section>
          )}

          {data && plans && (
            <div data-testid="readiness-summary" className="min-w-0 space-y-6">
              <section className="res-glass res-fade grid min-w-0 gap-5 rounded-2xl p-5 md:grid-cols-[auto_minmax(0,1fr)_minmax(0,1fr)] md:p-6">
                <div className="min-w-0">
                  <p className="text-[11px] uppercase tracking-wider text-muted-foreground">{t.stage}</p>
                  <p dir="ltr" data-testid="readiness-stage" className="rd-stage mt-1 font-mono text-4xl font-semibold text-primary">{data.configuration.stage}</p>
                  <p dir="ltr" className="mt-1 font-mono text-[11px] text-muted-foreground">{data.configuration.scenario}</p>
                  <p className="mt-3 max-w-sm text-[11px] leading-relaxed text-muted-foreground" data-testid="readiness-stage-context">{t.stageContext[data.configuration.stage]}</p>
                </div>
                <div className="min-w-0">
                  <p className="text-[11px] uppercase tracking-wider text-muted-foreground">{t.channels}</p>
                  <ul data-testid="readiness-channels" className="mt-2 flex flex-wrap gap-1.5">
                    {data.configuration.enabledChannelIds.map(c => (
                      <li key={c} className="res-chip max-w-full whitespace-normal break-words"><span dir="ltr" className="font-mono text-primary">{c}</span>{rt.chNames[c]}</li>
                    ))}
                  </ul>
                  <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground">{t.stageNote}</p>
                </div>
                <div data-testid="readiness-recommended" className="min-w-0 rounded-xl border border-white/10 bg-white/[.03] p-4">
                  <div className="grid grid-cols-2 gap-3">
                    <PlanTag label={t.baseline} id="P0" rt={rt} tone="cyan" />
                    {plans.recommended ? <PlanTag label={t.recommended} id={plans.recommended.id} rt={rt} tone="purple" /> : <div><p className="text-[11px] text-muted-foreground">{t.recommended}</p><p className="mt-1 text-sm">{t.unavailable}</p></div>}
                  </div>
                  {!plans.recommended && <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground">{t.noRec}</p>}
                  {plans.recommended?.id === 'P0' && <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground">{t.recIsBaseline}</p>}
                </div>
              </section>

              <section className="min-w-0">
                <SectionHead title={t.metricsTitle} sub={t.metricsSub} />
                <div className="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  {metricKeys.map((k, i) => (
                    <article key={k} className="res-glass res-fade min-w-0 rounded-2xl p-4" style={{ animationDelay: `${i * 70}ms` }}>
                      <h3 className="text-sm font-semibold">{rt.kpi[k]}</h3>
                      <div className="mt-3 grid grid-cols-2 gap-2">
                        {(['baseline', 'recommended'] as Side[]).map(s => {
                          const p = s === 'baseline' ? plans.baseline : plans.recommended;
                          return (
                            <div key={s} className={`min-w-0 rounded-lg border p-2.5 ${s === 'baseline' ? 'border-primary/20' : 'border-secondary/30'}`}>
                              <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{s === 'baseline' ? t.baseline : t.recommended}</p>
                              <p data-testid={`readiness-metric-${k}-${s}`} className="mt-1 flex min-w-0 flex-col font-mono text-lg font-semibold">{fmtMetric(p?.metrics[k] ?? null, t, language)}</p>
                            </div>
                          );
                        })}
                      </div>
                      <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground">{t.defs[k]}</p>
                    </article>
                  ))}
                </div>
              </section>

              <div className="grid min-w-0 grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
                <section className="res-glass min-w-0 rounded-2xl p-5">
                  <SectionHead icon={<Radio size={16} className="text-primary" />} title={t.channelsTitle} sub={t.channelsSub} />
                  <div className="space-y-3">
                    {CHS.map(ch => (
                      <div key={ch} className="min-w-0 rounded-xl border border-white/5 bg-white/[.02] p-3">
                        <p className="flex flex-wrap items-baseline gap-2 text-sm font-medium"><span dir="ltr" className="font-mono text-xs text-primary">{ch}</span>{rt.chNames[ch]}</p>
                        {ch === 'CH01' && <p className="text-[11px] text-muted-foreground">{rt.smsNote}</p>}
                        {ch === 'CH04' && <p className="text-[11px] text-muted-foreground">{rt.sirenNote}</p>}
                        <div className="mt-2 grid gap-2 sm:grid-cols-2">
                          {(['baseline', 'recommended'] as Side[]).map(s => (
                            <ChannelRow key={s} side={s} ch={ch} plan={s === 'baseline' ? plans.baseline : plans.recommended} t={t} rt={rt} lang={language} />
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>

                <div className="min-w-0 space-y-6">
                  <section className="res-glass min-w-0 rounded-2xl p-5">
                    <SectionHead icon={<Users size={16} className="text-secondary" />} title={t.accTitle} sub={t.accSub} />
                    <div className="grid grid-cols-2 gap-3">
                      {(['baseline', 'recommended'] as Side[]).map(s => {
                        const p = s === 'baseline' ? plans.baseline : plans.recommended;
                        return (
                          <div key={s} className="min-w-0 space-y-2">
                            <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{s === 'baseline' ? t.baseline : t.recommended}</p>
                            <div className="rounded-lg border border-white/10 p-2.5">
                              <p className="text-[11px] text-muted-foreground">{t.uniqueGaps}</p>
                              <p data-testid={`readiness-unique-gaps-${s}`} className="font-mono text-base font-semibold">{fmtCount(p?.accessibility?.uniqueResidentsWithGaps ?? null, t, language)}</p>
                            </div>
                            {p && !p.accessibility && <p className="text-[11px] text-muted-foreground">{t.accNone}</p>}
                            {groupIds.map(g => (
                              <div key={g} className="flex min-w-0 flex-wrap items-baseline justify-between gap-x-2 border-b border-white/5 pb-1.5">
                                <span className="min-w-0 text-[11px] text-muted-foreground">{rt.groups[g]}</span>
                                <span data-testid={`readiness-group-${s}-${g}`} className="font-mono text-xs">{fmtCount(p?.accessibility?.groups.find(x => x.id === g)?.residentsRequiringReview ?? null, t, language)}</span>
                              </div>
                            ))}
                          </div>
                        );
                      })}
                    </div>
                  </section>
                  <section className="res-glass min-w-0 rounded-2xl p-5">
                    <SectionHead icon={<Info size={16} className="text-primary" />} title={t.definitions} />
                    <ul className="space-y-2 text-xs leading-relaxed text-muted-foreground">
                      <li className="text-foreground/85">{t.causality}</li>
                      {t.defList.map(d => <li key={d}>{d}</li>)}
                    </ul>
                  </section>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
      {panel === 'notifications' && <Panel title={t.notifications} onClose={() => setPanel(null)}><p>{t.noNotifications}</p></Panel>}
      {typeof panel === 'number' && <Panel title={t.title} onClose={() => setPanel(null)}><p>{t.soon}</p></Panel>}
    </div>
  );
}

function fmtCount(n: number | null, t: ReadinessT, lang: string) {
  return n === null ? t.unavailable : `${n.toLocaleString(lang)} ${t.residents}`;
}
function fmtMetric(m: ResultMetric | null, t: ReadinessT, lang: string) {
  if (!m) return <span className="font-sans text-[11px] font-medium">{t.unavailable}</span>;
  if (m.unit === 'percent') return <span className="break-all">{m.value.toLocaleString(lang, { maximumFractionDigits: 20 })}{t.pct}</span>;
  return <><span className="break-all">{m.value.toLocaleString(lang)}</span>{' '}<span className="whitespace-nowrap font-sans text-[11px] font-normal text-muted-foreground">{t.residents}</span></>;
}

function SectionHead({ title, sub, icon }: { title: string; sub?: string; icon?: ReactNode }) {
  return (
    <div className="mb-4 min-w-0">
      <h2 className="flex items-center gap-2 text-lg font-semibold">{icon}{title}</h2>
      {sub && <p className="mt-0.5 text-xs text-muted-foreground">{sub}</p>}
    </div>
  );
}

function PlanTag({ label, id, rt, tone }: { label: string; id: string; rt: ResultsT; tone: 'cyan' | 'purple' }) {
  return (
    <div className="min-w-0">
      <p className="text-[11px] text-muted-foreground">{label}</p>
      <p className={`mt-1 font-mono text-xl font-semibold ${tone === 'cyan' ? 'text-primary' : 'text-secondary'}`}>{id}</p>
      <p className="text-[11px] leading-snug">{rt.planNames[id]}</p>
    </div>
  );
}

function ChannelRow({ side, ch, plan, t, rt, lang }: { side: Side; ch: string; plan: EvaluatedPlan | null; t: ReadinessT; rt: ResultsT; lang: string }) {
  const c = plan?.channels.find(x => x.id === ch) ?? null;
  return (
    <div data-testid={`readiness-channel-${side}-${ch}`} className={`min-w-0 rounded-lg border p-2 ${side === 'baseline' ? 'border-primary/15' : 'border-secondary/25'}`}>
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{side === 'baseline' ? t.baseline : t.recommended}</p>
      {c ? (
        <dl className="mt-1 grid grid-cols-[minmax(0,1fr)_auto] gap-x-2 gap-y-0.5 text-[11px]">
          {STATES.map(k => (
            <div key={k} className="contents">
              <dt className={`min-w-0 ${k === 'failed' || k === 'unavailable' ? 'text-[hsl(350_80%_75%)]' : k === 'delayed' ? 'text-[hsl(40_90%_70%)]' : 'text-muted-foreground'}`}>{rt.states[k]}</dt>
              <dd className="text-end font-mono">{c[k] === null ? t.unavailable : c[k]!.toLocaleString(lang)}</dd>
            </div>
          ))}
        </dl>
      ) : <p className="mt-1 text-[11px] text-muted-foreground">{plan ? t.noChannel : t.unavailable}</p>}
    </div>
  );
}
