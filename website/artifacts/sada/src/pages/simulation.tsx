import { useState } from 'react';
import { useLocation } from 'wouter';
import { ArrowLeft, ArrowRight, ShieldCheck } from 'lucide-react';
import { useLanguage } from '@/lib/i18n';
import { simulationT } from '@/lib/simulation-i18n';
import { usePlanning } from '@/lib/planning-state';
import { useLiveSimulation } from '@/lib/simulation-state';
import { Sidebar, Header, Panel, WaveLogo } from '@/components/shell';
import { MissionConfig } from '@/components/simulation/mission-config';
import { AgentWorkflow } from '@/components/simulation/agent-workflow';
import { ExecutionControl } from '@/components/simulation/execution-control';
import { OutputPanels } from '@/components/simulation/output-panels';
import '@/components/simulation/simulation.css';

export default function Simulation() {
  const { language, dir } = useLanguage();
  const t = simulationT[language];
  const rtl = dir === 'rtl';
  const { stage, enabledChannels } = usePlanning();
  const sim = useLiveSimulation();
  const [, navigate] = useLocation();
  const [menu, setMenu] = useState(false);
  const [panel, setPanel] = useState<null | 'notifications' | number>(null);
  const [focused, setFocused] = useState(0);
  const Back = rtl ? ArrowRight : ArrowLeft;

  return (
    <div dir="ltr" className="sada-home min-h-[100dvh] bg-background text-foreground">
      <Sidebar active={2} menu={menu} setMenu={setMenu} onNav={(i) => (i === 0 ? navigate('/') : i === 1 ? navigate('/planning') : i === 3 ? navigate('/results') : setPanel(i))} />
      <div className="lg:pl-60">
        <Header setMenu={setMenu} onNotifications={() => setPanel('notifications')} />
        <main dir={dir} className="relative mx-auto max-w-[1400px] space-y-6 px-4 pb-16 pt-5 md:px-8">
          {/* Mission hero */}
          <section className="relative overflow-hidden rounded-3xl border border-white/10">
            <img src={`${import.meta.env.BASE_URL}riyadh-dusk.jpg`} alt="" className="sim-backdrop absolute inset-0 h-full w-full object-cover object-[60%_40%]" />
            <div className="absolute inset-0 bg-[linear-gradient(90deg,hsl(229_55%_6%/.95)_0%,hsl(229_55%_6%/.7)_45%,hsl(250_50%_10%/.35)_100%)] rtl:bg-[linear-gradient(270deg,hsl(229_55%_6%/.95)_0%,hsl(229_55%_6%/.7)_45%,hsl(250_50%_10%/.35)_100%)]" />
            <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-background to-transparent" />
            <svg className="pointer-events-none absolute inset-0 h-full w-full opacity-60" viewBox="0 0 1000 300" preserveAspectRatio="none" aria-hidden>
              {[0, 1, 2].map((i) => <path key={i} className="dash" style={{ animationDuration: `${9 + i * 2}s` }} d={`M0 ${220 + i * 18} C300 ${150 + i * 20} 600 ${280 - i * 10} 1000 ${170 + i * 22}`} stroke={i % 2 ? 'hsl(270 75% 65%/.55)' : 'hsl(182 85% 55%/.55)'} strokeWidth="1" fill="none" />)}
            </svg>
            <div className="relative flex flex-col gap-6 p-6 md:flex-row md:items-end md:justify-between md:p-9">
              <div className="max-w-2xl rise">
                <div className="flex items-center gap-3">
                  <WaveLogo className="h-8 w-16" />
                  <span className="text-[11px] uppercase tracking-[0.24em] text-primary">{t.eyebrow}</span>
                </div>
                <h1 className="mt-3 text-3xl font-bold leading-tight md:text-5xl">{t.title}</h1>
                <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground md:text-[15px]">{t.lede}</p>
                <p className="mt-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[.04] px-3 py-1.5 text-[11px] text-muted-foreground backdrop-blur"><ShieldCheck size={13} className="text-primary" />{t.synthetic}</p>
              </div>
              <div className="rise flex flex-col gap-3 md:items-end" style={{ animationDelay: '120ms' }}>
                <div dir="ltr" className="flex flex-wrap items-center gap-2 font-mono text-xs">
                  <span className="sim-chip sim-chip-on text-sm" data-testid="hero-stage">{stage}</span>
                  <span className="sim-chip">AL_WADI_FLASH_FLOOD</span>
                  <span dir={dir} className="sim-chip">{t.population} <bdi dir="ltr" className="ms-1">1,000</bdi></span>
                  <span className="sim-chip">A · B · C</span>
                </div>
                <div dir="ltr" className="flex flex-wrap gap-1.5" data-testid="hero-channels">{enabledChannels.map((c) => <span key={c} className="sim-chip font-mono text-[11px]">{c}</span>)}</div>
                <button onClick={() => navigate('/planning')} className="inline-flex items-center gap-1.5 self-start text-xs text-muted-foreground transition hover:text-primary md:self-end"><Back size={13} />{t.back}</button>
              </div>
            </div>
          </section>

          <div className="grid gap-6 xl:grid-cols-[1fr_340px]">
            <AgentWorkflow t={t} focused={focused} setFocused={setFocused} status={sim.status} channels={enabledChannels} />
            <div className="space-y-6">
              <ExecutionControl t={t} rtl={rtl} status={sim.status} pending={sim.integrationPending} error={sim.error} resultId={sim.result?.id ?? null}
                onStart={() => { void sim.start(); }} onReset={sim.reset} onBack={() => navigate('/planning')}
                onResults={() => {
                  if (sim.status !== 'completed' || !sim.result?.id) return;
                  const configuration = sim.result.configuration;
                  const query = new URLSearchParams({
                    evaluationId: sim.result.id, scenario: configuration.scenario,
                    stage: configuration.stage, channels: configuration.enabledChannelIds.join(','),
                  });
                  navigate(`/results?${query}`);
                }} />
              <MissionConfig t={t} stage={stage} channels={enabledChannels} />
            </div>
          </div>

          <OutputPanels t={t} status={sim.status} outputs={sim.status === 'completed' && sim.result ? sim.result.outputs : null} />
          <p className="text-center text-[11px] text-muted-foreground/70">{t.ragNote}</p>
        </main>
      </div>
      {panel === 'notifications' && <Panel title={t.notifications} onClose={() => setPanel(null)}><p>{t.noNotifications}</p></Panel>}
      {typeof panel === 'number' && <Panel title={t.title} onClose={() => setPanel(null)}><p>{t.soon}</p></Panel>}
    </div>
  );
}
