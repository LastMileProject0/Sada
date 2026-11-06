import { useState, type ReactNode, type KeyboardEvent } from "react";
import { useLocation } from 'wouter';
import { useLanguage } from '@/lib/i18n';
import { planningT } from '@/lib/planning-i18n';
import { usePlanning, STAGES, CHANNEL_IDS, type ChannelId } from '@/lib/planning-state';
import { WaveLogo, Panel, Sidebar, Header } from '@/components/shell';
import {
  CalendarClock, RadioTower, Info, Clock, Crosshair, Users, MapPin, Gauge, Layers, Play,
  ArrowRight, Check, AlertTriangle, Lock, Radio, Cross, Siren, CloudLightning,
} from 'lucide-react';

const Id = ({ children, className = "", ...rest }: { children: ReactNode; className?: string; "data-testid"?: string }) => (
  <bdi {...rest} dir="ltr" className={`font-mono ${className}`} style={{ unicodeBidi: 'isolate' }}>{children}</bdi>
);

const hue: Record<ChannelId, number> = { CH01: 190, CH02: 205, CH03: 275, CH04: 182, CH05: 265 };

function ChannelArt({ id }: { id: ChannelId }) {
  const h = hue[id];
  const c = `hsl(${h} 90% 70%)`;
  const soft = `hsl(${h} 85% 55%/.35)`;
  return (
    <svg viewBox="0 0 120 80" className="h-full w-full" aria-hidden fill="none" strokeLinecap="round" strokeLinejoin="round">
      <defs>
        <radialGradient id={`g-${id}`}><stop offset="0" stopColor={`hsl(${h} 90% 60%/.55)`} /><stop offset="1" stopColor="transparent" /></radialGradient>
        <linearGradient id={`f-${id}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={`hsl(${h} 80% 55%/.45)`} /><stop offset="1" stopColor={`hsl(${h} 70% 25%/.25)`} /></linearGradient>
      </defs>
      <ellipse cx="60" cy="42" rx="44" ry="34" fill={`url(#g-${id})`} />
      {[0, 1, 2].map((k) => <ellipse key={k} cx="60" cy="70" rx={22 + k * 14} ry={4 + k * 2.5} stroke={soft} strokeWidth=".6" />)}
      {id === 'CH01' && <g stroke={c} strokeWidth="1.8" className="floaty">
        <path d="M34 20h52a8 8 0 0 1 8 8v20a8 8 0 0 1-8 8H58l-12 10v-10h-12a8 8 0 0 1-8-8V28a8 8 0 0 1 8-8z" fill={`url(#f-${id})`} />
        {[48, 60, 72].map((x) => <circle key={x} cx={x} cy="38" r="3" fill={c} stroke="none" />)}
      </g>}
      {id === 'CH02' && <g stroke={c} strokeWidth="1.8" className="floaty">
        <rect x="44" y="8" width="32" height="58" rx="6" fill={`url(#f-${id})`} />
        <path d="M54 13h12" /><path d="M50 40c4 0 5-8 10-8s6 8 10 8" strokeWidth="1.4" />
        <text x="60" y="52" fill={c} stroke="none" fontSize="6" textAnchor="middle" fontFamily="Sora">SADA</text>
        <path d="M82 18a10 10 0 0 1 0 14M88 13a18 18 0 0 1 0 24" strokeWidth="1.2" opacity=".7" />
      </g>}
      {id === 'CH03' && <g stroke={c} strokeWidth="1.8" className="floaty">
        <path d="M44 22c-4 4-4 12 4 22s18 16 24 12l4-4-8-8-5 3c-4-2-8-6-10-10l3-5-8-8z" fill={`url(#f-${id})`} />
        {[0, 1, 2].map((k) => <path key={k} d={`M${68 + k * 6} ${30 - k * 6}a${10 + k * 7} ${10 + k * 7} 0 0 1 ${8 + k * 4} ${10 + k * 6}`} strokeWidth="1.4" opacity={1 - k * 0.25} />)}
      </g>}
      {id === 'CH04' && <g stroke={c} strokeWidth="1.8" className="floaty">
        <path d="M36 32h10l22-14v40L46 44H36z" fill={`url(#f-${id})`} /><path d="M44 44l4 14h6l-3-12" />
        {[0, 1, 2].map((k) => <path key={k} d={`M${76 + k * 7} ${26 - k * 4}a${14 + k * 6} ${14 + k * 6} 0 0 1 0 ${24 + k * 8}`} strokeWidth="1.4" opacity={1 - k * 0.25} />)}
      </g>}
      {id === 'CH05' && <g stroke={c} strokeWidth="1.8" className="floaty">
        <rect x="30" y="12" width="60" height="40" rx="4" fill={`url(#f-${id})`} transform="rotate(-6 60 32)" />
        <path d="M60 22l10 18H50z" /><path d="M60 29v5M60 37v.5" /><path d="M56 54v14M66 53v15" />
      </g>}
    </svg>
  );
}

export default function Planning() {
  const { language, dir } = useLanguage();
  const p = planningT[language];
  const { stage, enabledChannels, setStage, toggleChannel, runEvaluation } = usePlanning();
  const [, navigate] = useLocation();
  const [menu, setMenu] = useState(false);
  const [panel, setPanel] = useState<null | number | 'notif' | 'run'>(null);
  const [blocked, setBlocked] = useState(false);
  const { t } = useLanguage();

  const onToggle = (id: ChannelId) => { setBlocked(!toggleChannel(id)); };
  const stageIdx = STAGES.indexOf(stage);
  const onStageKey = (e: KeyboardEvent<HTMLButtonElement>, i: number) => {
    const d = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0;
    if (!d) return;
    e.preventDefault();
    const n = (i + (dir === 'rtl' && e.key.startsWith('Arrow') && (e.key === 'ArrowRight' || e.key === 'ArrowLeft') ? -d : d) + STAGES.length) % STAGES.length;
    setStage(STAGES[n]);
    (document.querySelector(`[data-testid="stage-${STAGES[n]}"]`) as HTMLElement | null)?.focus();
  };

  return (
    <div dir="ltr" className="sada-home sada-planning relative min-h-[100dvh] overflow-hidden bg-[radial-gradient(ellipse_at_70%_0%,hsl(265_60%_18%),hsl(228_52%_7%)_60%)] text-foreground">
      <Sidebar active={1} menu={menu} setMenu={setMenu} onNav={(i) => (i === 0 ? navigate('/') : i === 2 ? navigate('/simulation') : i === 3 ? navigate('/results') : setPanel(i))} />
      <div className="lg:pl-60">
        <Header setMenu={setMenu} onNotifications={() => setPanel('notif')} />

        <main dir={dir} className="relative">
          {/* Hero */}
          <section className="relative min-h-[200px] overflow-hidden">
            <img src={`${import.meta.env.BASE_URL}riyadh-dusk.jpg`} alt="" className="absolute inset-0 h-full w-full object-cover object-[70%_30%] opacity-90 saturate-[1.25]" />
            <div className="absolute inset-0 bg-gradient-to-r from-[hsl(228_52%_7%)] via-[hsl(228_52%_7%/.6)] to-transparent" />
            <div className="absolute inset-0 bg-gradient-to-t from-[hsl(228_52%_7%)] via-transparent to-transparent" />
            <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>
              {[[60, 30, 72, 55], [72, 55, 86, 40], [86, 40, 94, 22], [60, 30, 68, 75], [68, 75, 86, 40]].map((l, i) => (
                <line key={i} x1={l[0]} y1={l[1]} x2={l[2]} y2={l[3]} stroke="hsl(190 85% 65%/.35)" strokeWidth="1" vectorEffect="non-scaling-stroke" className="dash" />
              ))}
              <ellipse cx="75" cy="95" rx="40" ry="16" fill="none" stroke="hsl(182 85% 55%/.35)" strokeWidth="1" vectorEffect="non-scaling-stroke" className="dash" />
            </svg>
            <div className="absolute inset-0 hidden md:block" aria-hidden>
              {[{ x: 60, y: 30, I: Radio, c: 182 }, { x: 72, y: 55, I: AlertTriangle, c: 0 }, { x: 86, y: 40, I: Users, c: 200 }, { x: 94, y: 22, I: CloudLightning, c: 270 }, { x: 68, y: 75, I: Cross, c: 300 }, { x: 52, y: 62, I: Siren, c: 270 }].map((m, i) => (
                <div key={i} className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: `${m.x}%`, top: `${m.y}%` }}>
                  <span className="absolute inset-0 rounded-full" style={{ background: `hsl(${m.c} 80% 60%/.4)`, animation: `pulse-ring 2.8s ease-out ${i * 0.4}s infinite` }} />
                  <div className="floaty relative grid h-9 w-9 place-items-center rounded-full border backdrop-blur-md" style={{ animationDelay: `${i * 0.6}s`, borderColor: `hsl(${m.c} 80% 65%/.7)`, background: `hsl(${m.c} 70% 25%/.45)`, boxShadow: `0 0 18px hsl(${m.c} 85% 55%/.55)` }}>
                    <m.I size={15} style={{ color: `hsl(${m.c} 90% 78%)` }} />
                  </div>
                </div>
              ))}
            </div>
            <div dir={dir} className="relative z-10 ml-0 mr-auto max-w-[720px] px-5 pb-6 pt-6 md:px-10">
              <WaveLogo className="rise mb-1 h-10 w-28 drop-shadow-[0_0_16px_hsl(182_90%_55%/.8)]" />
              <h1 data-testid="text-title" className="rise text-4xl font-bold md:text-[42px]" style={{ animationDelay: '.1s' }}>{p.title}</h1>
              <p className="rise mt-2 max-w-xl text-sm text-foreground/80 md:text-base" style={{ animationDelay: '.2s' }}>{p.subtitle}</p>
              <div className="mt-3 h-0.5 w-24 rounded-full bg-gradient-to-r from-primary to-secondary shadow-[0_0_12px_hsl(182_90%_55%)]" />
            </div>
          </section>

          <div dir="ltr" className="grid gap-5 px-5 pb-6 md:px-10 xl:grid-cols-[1fr_340px]">
            <div className="space-y-5">
              {/* Stage selector */}
              <section className="glass rise flex flex-col gap-4 rounded-2xl p-4 md:flex-row md:items-center" style={{ animationDelay: '.25s' }}>
                <div dir={dir} className="flex items-center gap-3 md:w-56">
                  <CalendarClock className="text-primary" size={22} />
                  <div><h2 id="stage-h" className="font-semibold">{p.stageTitle}</h2><p className="text-xs text-muted-foreground">{p.stageHint}</p></div>
                </div>
                <div dir={dir} role="radiogroup" aria-labelledby="stage-h" className="grid flex-1 grid-cols-2 gap-3 sm:grid-cols-4">
                  {STAGES.map((s, i) => {
                    const on = s === stage;
                    return (
                      <button key={s} role="radio" aria-checked={on} tabIndex={on ? 0 : -1} data-testid={`stage-${s}`} onClick={() => setStage(s)} onKeyDown={(e) => onStageKey(e, i)}
                        className={`relative flex items-center justify-center gap-2.5 rounded-xl border px-4 py-3 transition duration-300 ${on ? 'neon-border border-transparent bg-[hsl(182_80%_45%/.2)] text-primary shadow-[0_0_28px_-4px_hsl(182_90%_50%/.8)]' : 'border-[hsl(270_60%_60%/.3)] bg-[hsl(250_40%_14%/.5)] text-foreground/80 hover:-translate-y-0.5 hover:border-[hsl(270_70%_65%/.7)]'}`}>
                        <span className={`grid h-4 w-4 place-items-center rounded-full border-2 ${on ? 'border-primary' : 'border-white/40'}`}>{on && <span className="h-1.5 w-1.5 rounded-full bg-primary" />}</span>
                        <Id className="text-lg font-semibold">{s}</Id>
                      </button>
                    );
                  })}
                </div>
              </section>

              {/* Channels */}
              <section dir={dir} className="glass rise rounded-2xl p-4" style={{ animationDelay: '.35s' }} aria-labelledby="ch-h">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3"><RadioTower className="text-primary" size={22} /><h2 id="ch-h" className="font-semibold">{p.channelsTitle}</h2></div>
                  <p className="flex items-center gap-2 text-xs text-muted-foreground"><Info size={14} />{p.channelsHint}</p>
                </div>
                <div role="alert" data-testid="alert-last-channel" className={blocked ? 'mb-4 flex items-start gap-2 rounded-xl border border-[hsl(35_90%_60%/.5)] bg-[hsl(35_80%_40%/.15)] px-4 py-2.5 text-sm text-[hsl(38_95%_75%)]' : 'sr-only'}>
                  {blocked && <><AlertTriangle size={16} className="mt-0.5 shrink-0" />{p.lastChannel}</>}
                </div>
                <div dir="ltr" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                  {CHANNEL_IDS.map((id, i) => {
                    const on = enabledChannels.includes(id);
                    const ch = p.channels[id];
                    const h = hue[id];
                    return (
                      <article dir={dir} key={id} data-testid={`channel-${id}`} data-enabled={on}
                        className={`group relative flex flex-col overflow-hidden rounded-2xl border p-3 transition duration-500 hover:-translate-y-1 ${on ? '' : 'opacity-55 grayscale-[.6]'}`}
                        style={{ animation: `rise .9s cubic-bezier(.2,.7,.2,1) ${0.4 + i * 0.07}s both`, borderColor: `hsl(${h} 80% 62%/${on ? 0.55 : 0.2})`, background: `linear-gradient(170deg,hsl(${h} 60% 22%/.45),hsl(235 45% 10%/.6))`, boxShadow: on ? `0 0 30px -10px hsl(${h} 85% 55%/.8), inset 0 1px 0 hsl(0 0% 100%/.08)` : 'none' }}>
                        <Id className="self-start rounded-md border border-white/20 bg-white/5 px-2 py-0.5 text-[11px]">{id}</Id>
                        <div className="h-24"><ChannelArt id={id} /></div>
                        <h3 className="text-center text-[15px] font-semibold leading-tight">{ch.name}</h3>
                        <p className="mt-1.5 min-h-[2.5rem] text-center text-xs leading-snug text-muted-foreground">{ch.desc}</p>
                        <label className="mt-3 flex cursor-pointer items-center justify-between gap-2 border-t border-white/10 pt-3">
                          <span data-testid={`status-${id}`} className={`text-xs font-medium ${on ? 'text-primary' : 'text-muted-foreground'}`}>{on ? p.enabled : p.disabled}</span>
                          <button role="switch" aria-checked={on} aria-label={p.toggleLabel(ch.name)} data-testid={`toggle-${id}`} onClick={() => onToggle(id)}
                            className={`relative h-6 w-11 shrink-0 rounded-full border transition ${on ? 'border-primary/70 bg-[hsl(182_80%_45%/.45)] shadow-[0_0_14px_hsl(182_90%_50%/.6)]' : 'border-white/20 bg-white/10'}`}>
                            <span className={`absolute top-0.5 grid h-4.5 w-4.5 h-[18px] w-[18px] place-items-center rounded-full bg-[hsl(210_40%_94%)] transition-all ${on ? 'left-[22px]' : 'left-0.5'}`}>{on && <Check size={11} className="text-[hsl(228_52%_10%)]" />}</span>
                          </button>
                        </label>
                      </article>
                    );
                  })}
                </div>
              </section>
            </div>

            {/* Stage info */}
            <aside dir={dir} aria-labelledby="info-h" className="glass neon-border rise rounded-2xl p-5" style={{ animationDelay: '.3s' }}>
              <div className="mb-4 flex items-center justify-between gap-2">
                <h2 id="info-h" className="text-lg font-semibold">{p.infoTitle}</h2>
                <span className="flex items-center gap-1 text-[10px] text-muted-foreground"><Lock size={11} />{p.readonly}</span>
              </div>
              <dl className="space-y-4 text-sm">
                <Row icon={Clock} label={p.snapshot}>
                  <Id className="rounded-lg border border-primary/60 bg-[hsl(182_80%_45%/.15)] px-3 py-1 text-base font-semibold text-primary shadow-[0_0_14px_-2px_hsl(182_90%_50%/.7)]">{stage}</Id>
                </Row>
                <p key={stage} role="status" data-testid="text-stage-description" className="rise rounded-xl border border-white/10 bg-white/[.03] p-3 text-[13px] leading-relaxed" style={{ animationDuration: '.5s' }}>
                  <span className="sr-only">{p.statusStage(stage)}. </span>{p.stages[stage]}
                  {stageIdx > 0 && <span className="mt-1 block text-[11px] text-muted-foreground">{p.cumulative}</span>}
                </p>
                <Row icon={Crosshair} label={p.scenario}><Id className="rounded-md border border-secondary/50 bg-secondary/10 px-2 py-1 text-[12px]">AL_WADI_FLASH_FLOOD</Id></Row>
                <Row icon={Users} label={p.population}><span className="text-end"><Id className="block text-lg font-semibold">1000</Id><span className="text-[11px] text-muted-foreground">{p.populationValue}</span></span></Row>
                <Row icon={MapPin} label={p.zones}><span className="flex gap-2">{['A', 'B', 'C'].map((z) => <Id key={z} className="grid h-8 w-9 place-items-center rounded-lg border border-primary/40 bg-white/5">{z}</Id>)}</span></Row>
                <div className="flex gap-3 border-t border-white/10 pt-4">
                  <Gauge size={18} className="mt-0.5 shrink-0 text-primary" />
                  <div><dt className="font-medium">{p.boundaries}</dt><dd className="mt-1 text-xs leading-relaxed text-muted-foreground">{p.boundariesText}</dd></div>
                </div>
              </dl>
            </aside>
          </div>

          {/* Summary */}
          <section aria-labelledby="sum-h" className="px-5 pb-10 md:px-10">
            <div dir="ltr" className="glass rise relative flex flex-col gap-5 overflow-hidden rounded-2xl p-5 lg:flex-row lg:items-center" style={{ animationDelay: '.6s' }}>
              <svg className="pointer-events-none absolute inset-x-0 bottom-0 h-16 w-full opacity-50" viewBox="0 0 400 60" preserveAspectRatio="none" aria-hidden>
                {[0, 1, 2].map((i) => <path key={i} className="dash" d={`M0 ${40 + i * 6} C100 ${20 + i * 8} 200 ${55 - i * 4} 400 ${30 + i * 6}`} stroke={i % 2 ? 'hsl(270 70% 62%/.5)' : 'hsl(182 85% 55%/.5)'} strokeWidth=".8" fill="none" />)}
              </svg>
              <div dir={dir} className="flex items-center gap-4 lg:w-64">
                <div className="relative grid h-16 w-16 shrink-0 place-items-center">
                  <span className="absolute inset-0 rounded-full bg-primary/30" style={{ animation: 'pulse-ring 3s ease-out infinite' }} />
                  <span className="relative grid h-14 w-14 place-items-center rounded-full border border-primary/60 bg-[hsl(182_70%_25%/.4)] shadow-[0_0_24px_hsl(182_90%_50%/.6)]"><WaveLogo className="h-7 w-12" /></span>
                </div>
                <h2 id="sum-h" className="text-lg font-semibold">{p.summaryTitle}</h2>
              </div>
              <div dir={dir} className="relative flex-1 space-y-3 border-white/10 lg:border-s lg:ps-6">
                <div className="flex items-center gap-3 text-sm"><Clock size={16} className="text-primary" /><span className="w-40 text-muted-foreground">{p.selectedStage}</span><Id className="rounded-lg border border-primary/50 px-3 py-1 text-primary" data-testid="summary-stage">{stage}</Id></div>
                <div className="flex flex-wrap items-center gap-3 text-sm">
                  <Layers size={16} className="text-primary" />
                  <span className="w-40 text-muted-foreground" data-testid="enabled-count" aria-live="polite">{p.enabledChannels(enabledChannels.length)}</span>
                  <span className="flex flex-wrap gap-2" data-testid="summary-channels">
                    {CHANNEL_IDS.map((id) => {
                      const on = enabledChannels.includes(id);
                      return (
                        <span key={id} className={`flex flex-col items-center gap-0.5 rounded-lg border px-2.5 py-1 text-xs transition ${on ? 'border-primary/50 bg-[hsl(182_80%_45%/.12)]' : 'border-white/10 text-muted-foreground/50 line-through'}`}>
                          <Id>{id}</Id>
                          <span className={`grid h-3.5 w-3.5 place-items-center rounded-full ${on ? 'bg-primary text-primary-foreground' : 'bg-white/10'}`}>{on && <Check size={9} />}</span>
                          <span className="sr-only">{on ? p.enabled : p.disabled}</span>
                        </span>
                      );
                    })}
                  </span>
                </div>
              </div>
              <button data-testid="run-evaluation" onClick={() => { runEvaluation(); navigate('/simulation'); }}
                className="group neon-border relative flex items-center justify-between gap-6 rounded-2xl bg-gradient-to-br from-[hsl(182_80%_40%/.6)] to-[hsl(190_70%_22%/.6)] px-7 py-5 text-xl font-semibold shadow-[0_0_40px_-6px_hsl(182_90%_50%/.8)] transition hover:-translate-y-0.5 hover:shadow-[0_0_56px_-4px_hsl(182_90%_50%/1)] lg:min-w-[280px]">
                <span className="grid h-10 w-10 place-items-center rounded-full border border-white/50"><Play size={16} fill="currentColor" /></span>
                <span>{p.run}</span>
                <ArrowRight size={20} className={`transition group-hover:translate-x-1 ${dir === 'rtl' ? 'rotate-180' : ''}`} />
              </button>
            </div>
          </section>
        </main>
      </div>

      {panel === 'run' && <Panel title={p.pendingTitle} onClose={() => setPanel(null)}>
        <p data-testid="text-pending">{p.pendingBody}</p>
        <p>{p.pendingSaved}</p>
        <div className="flex flex-wrap items-center gap-2 text-foreground">
          <Id className="rounded-md border border-primary/50 px-2 py-0.5 text-primary">{stage}</Id>
          {enabledChannels.map((c) => <Id key={c} className="rounded-md border border-white/20 px-2 py-0.5">{c}</Id>)}
        </div>
        <p className="text-xs">{p.pendingNoResults}</p>
      </Panel>}
      {typeof panel === 'number' && <Panel title={t.nav[panel]} onClose={() => setPanel(null)}><p>{p.comingSoon}</p></Panel>}
      {panel === 'notif' && <Panel title={t.notifications} onClose={() => setPanel(null)}><p>{t.noNotifications}</p></Panel>}
    </div>
  );
}

function Row({ icon: I, label, children }: { icon: typeof Clock; label: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="flex items-center gap-3"><I size={18} className="text-primary" />{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}
