import { useState } from 'react';
import { useLocation } from 'wouter';
import { WaveLogo, Panel, Sidebar, Header } from '@/components/shell';
import { useLanguage } from '@/lib/i18n';
import {
  ShieldCheck, ArrowRight, Play, ClipboardCheck, Accessibility, BarChart3, Radio, AlertTriangle,
  Users, CloudLightning, Cross, Siren, Ear, Eye, Hand,
} from 'lucide-react';

const features = [
  { icon: ClipboardCheck, hue: 182 },
  { icon: Accessibility, hue: 270 },
  { icon: BarChart3, hue: 196 },
  { icon: ShieldCheck, hue: 285 },
];

const metrics = [
  { v: '1000' },
  { v: '5' },
  { v: '4' },
  { v: null },
];

const markers = [
  { x: 58, y: 22, icon: Radio, c: 182 }, { x: 64, y: 44, icon: AlertTriangle, c: 0 },
  { x: 84, y: 40, icon: Users, c: 200 }, { x: 89, y: 18, icon: CloudLightning, c: 270 },
  { x: 74, y: 70, icon: Cross, c: 300 }, { x: 52, y: 58, icon: Siren, c: 270 },
];

function Sparkline() {
  return (
    <svg viewBox="0 0 100 30" className="h-8 w-full">
      <defs><linearGradient id="sg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="hsl(182 85% 55%/.4)" /><stop offset="1" stopColor="transparent" /></linearGradient></defs>
      <path d="M0 24 L12 20 L24 22 L36 14 L48 16 L60 9 L72 12 L84 5 L100 7 L100 30 L0 30Z" fill="url(#sg)" />
      <path d="M0 24 L12 20 L24 22 L36 14 L48 16 L60 9 L72 12 L84 5 L100 7" fill="none" stroke="hsl(182 85% 60%)" strokeWidth="1.2" />
    </svg>
  );
}

export default function Home() {
  const { language, t, dir } = useLanguage();
  const [, navigate] = useLocation();
  const [panel, setPanel] = useState<null | 'start' | 'how' | number>(null);
  const [menu, setMenu] = useState(false);

  return (
    <div dir="ltr" className="sada-home relative min-h-[100dvh] overflow-hidden bg-[radial-gradient(ellipse_at_70%_0%,hsl(265_60%_18%),hsl(228_52%_7%)_60%)] text-foreground">
      <Sidebar active={0} menu={menu} setMenu={setMenu} onNav={(i) => (i === 1 ? navigate('/planning') : i === 2 ? navigate('/simulation') : i === 3 ? navigate('/results') : setPanel(100 + i))} />

      <div className="lg:pl-60">
        <Header setMenu={setMenu} onNotifications={() => setPanel(200)} />

        {/* Hero */}
        <section className="relative min-h-[380px] overflow-hidden">
          <img src={`${import.meta.env.BASE_URL}riyadh-dusk.jpg`} alt="" className="absolute inset-0 h-full w-full scale-105 object-cover object-[70%_50%] opacity-80" />
          <div className="absolute inset-0 bg-gradient-to-r from-[hsl(228_52%_7%)] via-[hsl(228_52%_7%/.75)] to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-t from-[hsl(228_52%_7%)] via-transparent to-[hsl(228_52%_7%/.3)]" />
          {/* holographic arcs */}
          <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>
            {[30, 42, 54].map((r, i) => (
              <ellipse key={r} cx="72" cy="78" rx={r * 0.9} ry={r * 0.35} fill="none" stroke={i % 2 ? 'hsl(270 75% 65%/.35)' : 'hsl(182 85% 55%/.35)'} strokeWidth=".15" className="dash" vectorEffect="non-scaling-stroke" />
            ))}
            {markers.map((m, i) => markers.slice(i + 1, i + 3).map((n, j) => (
              <line key={`${i}-${j}`} x1={m.x} y1={m.y} x2={n.x} y2={n.y} stroke="hsl(190 85% 65%/.25)" strokeWidth="1" vectorEffect="non-scaling-stroke" className="dash" />
            )))}
          </svg>
          <div className="absolute inset-0 hidden md:block" aria-hidden>
            {markers.map((m, i) => (
              <div key={i} className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: `${m.x}%`, top: `${m.y}%` }}>
                <span className="absolute inset-0 rounded-full" style={{ background: `hsl(${m.c} 80% 60%/.4)`, animation: `pulse-ring 2.8s ease-out ${i * 0.4}s infinite` }} />
                <div className="floaty relative grid h-11 w-11 place-items-center rounded-full border backdrop-blur-md" style={{ animationDelay: `${i * 0.7}s`, borderColor: `hsl(${m.c} 80% 65%/.7)`, background: `hsl(${m.c} 70% 25%/.45)`, boxShadow: `0 0 22px hsl(${m.c} 85% 55%/.55)` }}>
                  <m.icon size={18} style={{ color: `hsl(${m.c} 90% 78%)` }} />
                </div>
              </div>
            ))}
          </div>
          {Array.from({ length: 18 }).map((_, i) => (
            <span key={i} aria-hidden className="absolute h-1 w-1 rounded-full bg-primary" style={{ left: `${(i * 53) % 100}%`, bottom: `${(i * 17) % 40}%`, animation: `drift ${6 + (i % 5)}s linear ${i * 0.6}s infinite`, opacity: 0 }} />
          ))}

          <div className="relative z-10 px-6 pb-6 pt-5 md:px-12 md:pt-7">
            <div className="rise relative inline-block">
              <div className="absolute -inset-10 rounded-full bg-[hsl(182_90%_50%/.18)] blur-3xl" />
              <WaveLogo className="relative mb-1 h-12 w-32 drop-shadow-[0_0_18px_hsl(182_90%_55%/.8)]" />
            </div>
            <h1 dir="ltr" className="brand-lockup rise flex items-baseline gap-4 text-5xl font-bold md:text-6xl" style={{ animationDelay: '.1s' }}>
              <span lang="ar" className="ar drop-shadow-[0_0_24px_hsl(182_90%_60%/.35)]">صدى</span>
              <span className="font-light text-primary/60">|</span>
              <span lang="en" className="bg-gradient-to-r from-white to-[hsl(190_80%_80%)] bg-clip-text tracking-[0.12em] text-transparent">SADA</span>
            </h1>
            <p dir={dir} className="rise mt-3 max-w-lg text-start text-2xl font-medium md:text-[26px]" style={{ animationDelay: '.2s' }}>{t.heading}</p>

            <div className="rise mt-6 flex flex-wrap gap-4" style={{ animationDelay: '.35s' }}>
              <button data-testid="button-start-planning" onClick={() => navigate('/planning')}
                className="group neon-border relative flex items-center gap-5 rounded-xl bg-gradient-to-br from-[hsl(182_80%_40%/.55)] to-[hsl(190_70%_25%/.5)] px-6 py-3 shadow-[0_0_30px_-6px_hsl(182_90%_50%/.7)] transition hover:-translate-y-0.5 hover:shadow-[0_0_44px_-4px_hsl(182_90%_50%/.9)]">
                <span dir={dir} className="font-semibold leading-tight">{t.start}</span>
                <ArrowRight size={18} className={`transition group-hover:translate-x-1 ${language === 'ar' ? 'rotate-180' : ''}`} />
              </button>
              <button data-testid="button-explore" onClick={() => setPanel('how')}
                className="group glass flex items-center gap-4 rounded-xl border-[hsl(270_70%_62%/.5)] px-6 py-3 shadow-[0_0_26px_-8px_hsl(270_80%_60%/.7)] transition hover:-translate-y-0.5">
                <span className="grid h-8 w-8 place-items-center rounded-full border border-white/40"><Play size={13} fill="currentColor" /></span>
                <span dir={dir} className="font-semibold leading-tight">{t.explore}</span>
              </button>
            </div>

            <div className="rise mt-5 flex flex-wrap gap-3" style={{ animationDelay: '.45s' }}>
              {metrics.map((m, i) => (
                <div dir={dir} key={i} data-testid={`metric-${i}`} className="glass flex items-center gap-3 rounded-full py-1.5 pl-1.5 pr-4">
                  <span className="rounded-full bg-[hsl(182_80%_45%/.15)] px-2.5 py-1 font-mono text-sm text-primary">{m.v ?? t.accessibility}</span>
                  <span className="text-xs leading-tight text-muted-foreground">{t.metrics[i]}</span>
                </div>
              ))}
              <span dir={dir} className="self-center font-mono text-[10px] uppercase tracking-widest text-muted-foreground/60">{t.illustrative}</span>
            </div>
          </div>
        </section>

        {/* Features + lower-right intelligence */}
        <section className="relative px-5 pb-14 md:px-12">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((f, i) => (
              <button dir={dir} key={i} data-testid={`card-feature-${i}`} onClick={() => i === 2 ? navigate('/results') : setPanel(i)}
                className="group glass rise relative overflow-hidden rounded-2xl p-5 text-start transition duration-500 hover:-translate-y-1.5"
                style={{ animationDelay: `${0.5 + i * 0.08}s`, boxShadow: `inset 0 1px 0 hsl(0 0% 100%/.08), 0 0 0 1px hsl(${f.hue} 80% 60%/.25), 0 24px 50px -24px hsl(${f.hue} 80% 50%/.55)` }}>
                <div className="absolute -right-12 -top-12 h-40 w-40 rounded-full opacity-40 blur-3xl transition group-hover:opacity-80" style={{ background: `hsl(${f.hue} 85% 55%)` }} />
                <div className="relative mb-3 flex h-20 items-center justify-center">
                  <svg className="absolute inset-0 h-full w-full opacity-40" viewBox="0 0 200 100" aria-hidden>
                    {[0, 1, 2, 3].map((k) => <ellipse key={k} cx="100" cy="70" rx={30 + k * 22} ry={8 + k * 6} fill="none" stroke={`hsl(${f.hue} 80% 65%)`} strokeWidth=".5" />)}
                  </svg>
                  <div className="floaty relative grid h-16 w-16 place-items-center rounded-2xl border transition group-hover:scale-110" style={{ animationDelay: `${i}s`, borderColor: `hsl(${f.hue} 85% 65%/.6)`, background: `linear-gradient(145deg,hsl(${f.hue} 70% 40%/.5),hsl(${f.hue} 70% 18%/.4))`, boxShadow: `0 0 34px hsl(${f.hue} 85% 55%/.55), inset 0 1px 0 hsl(0 0% 100%/.2)` }}>
                    <f.icon size={30} strokeWidth={1.5} style={{ color: `hsl(${f.hue} 95% 82%)` }} />
                  </div>
                  {i === 1 && [Ear, Eye, Hand].map((I, k) => (
                    <span key={k} className="floaty absolute grid h-8 w-8 place-items-center rounded-full border border-white/20 bg-white/5" style={{ left: `${[12, 78, 70][k]}%`, top: `${[20, 8, 70][k]}%`, animationDelay: `${k * 0.8}s` }}><I size={14} /></span>
                  ))}
                </div>
                <h3 className="relative text-lg font-bold">{t.features[i]}</h3>
                <div className="relative mt-4 flex items-end justify-between gap-3 border-t border-white/10 pt-4">
                  <p className="text-xs leading-relaxed text-muted-foreground">{t.descriptions[i]}</p>
                  <ArrowRight size={16} className={`shrink-0 transition group-hover:translate-x-1 ${language === 'ar' ? 'rotate-180' : ''}`} style={{ color: `hsl(${f.hue} 90% 70%)` }} />
                </div>
              </button>
            ))}
          </div>

          <aside dir={dir} className="glass rise relative mt-5 overflow-hidden rounded-2xl p-5 opacity-80 lg:ml-auto lg:max-w-md" style={{ animationDelay: '.8s' }} aria-label={t.previewLabel}>
            <div className="absolute inset-0 opacity-20 [background-image:linear-gradient(hsl(190_80%_60%/.3)_1px,transparent_1px),linear-gradient(90deg,hsl(190_80%_60%/.3)_1px,transparent_1px)] [background-size:22px_22px]" />
            <div className="relative">
              <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-widest text-muted-foreground"><span>{t.preview}</span><span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-primary shadow-[0_0_6px_hsl(182_90%_55%)]" />{t.demo}</span></div>
              <p className="mt-3 text-sm font-medium">{t.curve}</p>
              <div className="mt-3"><Sparkline /></div>
              <div className="mt-4 space-y-2.5">
                {[82, 64, 47, 58, 71].map((v, i) => (
                  <div key={i} className="text-[11px]">
                    <div className="mb-1 flex justify-between text-muted-foreground"><span>{t.channels[i]}</span><span className="font-mono">{v}</span></div>
                    <div className="h-1 rounded-full bg-white/5"><div className="h-full rounded-full bg-gradient-to-r from-primary to-secondary" style={{ width: `${v}%` }} /></div>
                  </div>
                ))}
              </div>
              <div className="mt-5 flex items-center gap-3">
                <svg viewBox="0 0 40 40" className="h-14 w-14 -rotate-90"><circle cx="20" cy="20" r="16" fill="none" stroke="hsl(0 0% 100%/.08)" strokeWidth="3" /><circle cx="20" cy="20" r="16" fill="none" stroke="hsl(270 75% 65%)" strokeWidth="3" strokeDasharray="100" strokeDashoffset="28" pathLength="100" strokeLinecap="round" /></svg>
                <p className="text-[11px] leading-snug text-muted-foreground">{t.agents} <span className="text-foreground/70">{t.samples}</span></p>
              </div>
            </div>
          </aside>
        </section>
      </div>

      {panel === 'start' && <Panel title={t.start} onClose={() => setPanel(null)}>
        <p>{t.planningIntro}</p>
        <p>{t.planningNote}</p>
      </Panel>}
      {panel === 'how' && <Panel title={t.how} onClose={() => setPanel(null)}>
        <ol className="list-decimal space-y-2 ps-5">
          {t.steps.map((step) => <li key={step}>{step}</li>)}
        </ol>
        <p className="text-xs">{t.concept}</p>
        <button data-testid="link-about-limits" onClick={() => navigate('/about')} className="text-primary underline underline-offset-4">{t.aboutLink}</button>
      </Panel>}
      {typeof panel === 'number' && panel < 100 && <Panel title={t.features[panel]} onClose={() => setPanel(null)}>
        <p className="text-foreground/85">{t.descriptions[panel]}</p>
        <p className="text-xs">{t.moduleNote}</p>
      </Panel>}
      {typeof panel === 'number' && panel >= 100 && panel < 200 && <Panel title={t.nav[panel - 100]} onClose={() => setPanel(null)}>
        <p>{t.comingSoon}</p>
      </Panel>}
      {panel === 200 && <Panel title={t.notifications} onClose={() => setPanel(null)}><p>{t.noNotifications}</p></Panel>}
    </div>
  );
}
