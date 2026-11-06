import { type KeyboardEvent } from 'react';
import { ChevronDown } from 'lucide-react';
import type { SimulationDict } from '@/lib/simulation-i18n';
import { AgentArt } from './agent-art';
import type { ExecutionStatus } from '@/lib/simulation';

const legendColors = [
  ['hsl(160 80% 55%)', 'hsl(42 95% 60%)', 'hsl(352 85% 62%)', 'hsl(220 15% 55%)'],
  ['hsl(352 85% 62%)', 'hsl(42 95% 60%)', 'hsl(182 90% 60%)'],
  ['hsl(182 90% 60%)', 'hsl(220 15% 55%)'],
  ['hsl(220 20% 75%)', 'hsl(182 90% 60%)', 'hsl(230 85% 68%)', 'hsl(270 80% 70%)'],
];

export function AgentWorkflow({ t, focused, setFocused, status, channels }: { t: SimulationDict; focused: number; setFocused: (i: number) => void; status: ExecutionStatus; channels: string[] }) {
  const onKey = (e: KeyboardEvent<HTMLButtonElement>, i: number) => {
    const rtl = document.documentElement.dir === 'rtl';
    let n = i;
    if (e.key === (rtl ? 'ArrowLeft' : 'ArrowRight') || e.key === 'ArrowDown') n = Math.min(3, i + 1);
    else if (e.key === (rtl ? 'ArrowRight' : 'ArrowLeft') || e.key === 'ArrowUp') n = Math.max(0, i - 1);
    else return;
    e.preventDefault(); setFocused(n);
    document.querySelector<HTMLButtonElement>(`[data-testid="agent-${n + 1}"]`)?.focus();
  };
  const a = t.agents[focused];
  return (
    <section aria-labelledby="wf-h" className="glass neon-border relative overflow-hidden rounded-3xl p-5 md:p-7">
      <div className="sim-grid pointer-events-none absolute inset-0 opacity-40" />
      <div className="relative flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="wf-h" className="text-lg font-semibold">{t.workflow}</h2>
          <p className="mt-1 max-w-xl text-xs text-muted-foreground">{t.workflowNote}</p>
        </div>
        <span data-testid="workflow-status" className="rounded-full border border-white/10 px-3 py-1 text-[11px] text-muted-foreground">{t.statuses[status]}</span>
      </div>

      <div className="relative mt-7">
        {/* Illustrative connection rail */}
        <svg className="pointer-events-none absolute inset-x-0 top-[62px] hidden h-10 w-full md:block" viewBox="0 0 1000 40" preserveAspectRatio="none" aria-hidden>
          <defs><linearGradient id="rail" x1="0" x2="1"><stop offset="0" stopColor="hsl(182 90% 60%)" /><stop offset="1" stopColor="hsl(270 80% 70%)" /></linearGradient></defs>
          <path d="M125 20 C250 0 250 40 375 20 S500 0 625 20 S750 40 875 20" stroke="url(#rail)" strokeOpacity=".25" strokeWidth="6" fill="none" />
          <path d="M125 20 C250 0 250 40 375 20 S500 0 625 20 S750 40 875 20" stroke="url(#rail)" strokeWidth="1.5" fill="none" className="dash" />
          <circle r="3.5" fill="hsl(182 90% 70%)" className="sim-pulse-dot"><animateMotion dur="7s" repeatCount="indefinite" path="M125 20 C250 0 250 40 375 20 S500 0 625 20 S750 40 875 20" /></circle>
        </svg>
        <ol role="tablist" aria-label={t.workflow} className="relative grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-5">
          {t.agents.map((ag, i) => {
            const on = i === focused;
            return (
              <li key={i} role="presentation">
                <button id={`agent-${i + 1}`} role="tab" aria-selected={on} aria-controls="agent-detail" tabIndex={on ? 0 : -1} data-testid={`agent-${i + 1}`}
                  onClick={() => setFocused(i)} onKeyDown={(e) => onKey(e, i)}
                  className={`sim-agent group relative flex w-full flex-col items-center rounded-2xl px-3 pb-4 pt-3 text-center transition duration-300 ${on ? 'sim-agent-on' : ''}`}>
                  <span dir="ltr" className="self-start font-mono text-[10px] tracking-[0.2em] text-muted-foreground">0{i + 1}</span>
                  <span className="relative grid h-24 w-24 place-items-center">
                    {on && <span className="absolute inset-2 rounded-full border border-primary/40 sim-halo" />}
                    <AgentArt index={i} className="relative h-20 w-20 transition-transform duration-500 group-hover:scale-105" />
                  </span>
                  <span className="mt-1 text-[13px] font-semibold leading-tight">{ag.name}</span>
                  <span className={`mt-2 inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] ${on ? 'bg-primary/15 text-primary' : 'text-muted-foreground'}`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${on ? 'bg-primary' : 'border border-white/30'}`} />
                    {on ? t.selected : t.inspect}
                  </span>
                </button>
              </li>
            );
          })}
        </ol>
      </div>

      <div id="agent-detail" role="tabpanel" aria-labelledby={`agent-${focused + 1}`} key={focused} className="rise relative mt-6 grid gap-5 rounded-2xl border border-white/10 bg-[hsl(230_50%_8%/.55)] p-5 md:grid-cols-[1.3fr_1fr]">
        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-primary">{t.agent} <span dir="ltr" className="font-mono">0{focused + 1}</span></p>
          <h3 className="mt-1 text-xl font-semibold">{a.name}</h3>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{a.short}</p>
          <ul className="mt-4 space-y-2">
            {a.points.map((p) => <li key={p} className="flex gap-2.5 text-[13px]"><span className="mt-[7px] h-1 w-3 shrink-0 rounded bg-gradient-to-r from-primary to-secondary" />{p}</li>)}
          </ul>
          {focused === 0 && <div dir="ltr" className="mt-4 flex flex-wrap gap-1.5">{channels.map((c) => <span key={c} className="sim-chip">{c}</span>)}</div>}
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[.02] p-4">
          <p className="text-xs font-medium text-muted-foreground">{a.legendTitle}</p>
          <ul className="mt-3 space-y-2.5">
            {a.legend.map((l, j) => (
              <li key={l} className="flex items-center justify-between gap-3 text-[13px]">
                <span className="flex items-center gap-2.5"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: legendColors[focused][j], boxShadow: `0 0 10px ${legendColors[focused][j]}` }} /><bdi>{l}</bdi></span>
                <span className="text-[11px] text-muted-foreground/70">{t.legendOnly}</span>
              </li>
            ))}
          </ul>
          <p className="mt-4 flex items-center gap-1.5 border-t border-white/5 pt-3 text-[11px] text-muted-foreground">
            <ChevronDown size={12} className="-rotate-90 rtl:rotate-90" />
            {focused < 3 ? <>{t.handoff} <span className="text-foreground">{t.agents[focused + 1].name}</span></> : t.final}
          </p>
        </div>
      </div>
    </section>
  );
}
