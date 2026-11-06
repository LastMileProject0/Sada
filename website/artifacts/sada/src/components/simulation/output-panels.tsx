import type { SimulationDict, OutputKey } from '@/lib/simulation-i18n';
import { PolicyAssistant } from './policy-assistant';
import type { ExecutionStatus } from '@/lib/simulation';

const keys: OutputKey[] = ['delivery', 'risk', 'accessibility', 'policy', 'recovery', 'trace'];
type Item = { label: string; detail: string };

function Glyph({ k }: { k: OutputKey }) {
  const s = { stroke: 'currentColor', strokeWidth: 1.5, fill: 'none', strokeLinecap: 'round' as const };
  return (
    <svg viewBox="0 0 48 48" className="h-10 w-10 text-primary/70" aria-hidden>
      <circle cx="24" cy="24" r="21" {...s} strokeDasharray="2 4" opacity=".4" />
      {k === 'delivery' && <path d="M12 30 Q24 10 36 30 M18 30 Q24 20 30 30" {...s} />}
      {k === 'risk' && <path d="M24 13 L35 33 H13 Z M24 21 V27" {...s} />}
      {k === 'accessibility' && <path d="M24 14 a2 2 0 1 0 .1 0 M16 21 H32 M24 21 V29 L19 35 M24 29 L29 35" {...s} />}
      {k === 'policy' && <path d="M24 12 L34 16 V24 C34 30 29 34 24 36 C19 34 14 30 14 24 V16 Z M20 24 l3 3 l5 -6" {...s} />}
      {k === 'recovery' && <path d="M14 34 V26 M21 34 V20 M28 34 V24 M35 34 V16" {...s} />}
      {k === 'trace' && <path d="M14 15 H34 M14 22 H30 M14 29 H34 M14 36 H24" {...s} />}
    </svg>
  );
}

export function OutputPanels({ t, outputs, status }: { t: SimulationDict; outputs: Record<OutputKey, Item[]> | null; status: ExecutionStatus }) {
  return (
    <section aria-labelledby="out-h">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
        <h2 id="out-h" className="text-lg font-semibold">{t.outputs}</h2>
        <p className="text-xs text-muted-foreground">{t.outputsNote}</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {keys.map((k, i) => {
          const items = outputs?.[k] ?? [];
          return (
            <article key={k} data-testid={`output-${k}`} className="sim-out glass group relative min-h-[170px] overflow-hidden rounded-2xl p-5 rise" style={{ animationDelay: `${i * 70}ms` }}>
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-sm font-semibold">{t.outputNames[k]}</h3>
                <span dir="ltr" className="font-mono text-[10px] text-muted-foreground/60">0{i + 1}</span>
              </div>
              {items.length ? (
                <ul className="mt-3 space-y-2">{items.map((it, j) => <li key={j} className="text-[13px]"><p className="font-medium">{it.label}</p><p className="text-xs text-muted-foreground">{it.detail}</p></li>)}</ul>
              ) : (
                <div className="mt-4 flex items-center gap-4">
                  <Glyph k={k} />
                  <div>
                    <p data-testid={`output-${k}-state`} className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground/80">{status === 'completed' ? t.noOutput : status === 'not_started' ? t.awaiting : t.statuses[status]}</p>
                    <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{status === 'completed' ? t.noOutputBody : status === 'error' ? t.errorBody : t.outputHints[k]}</p>
                  </div>
                </div>
              )}
              <div className="mt-5 space-y-1.5" aria-hidden>
                {!items.length && [72, 54, 38].map((w) => <div key={w} className="h-1.5 rounded-full bg-white/[.04]" style={{ width: `${w}%` }} />)}
              </div>
              {k === 'policy' && <PolicyAssistant />}
            </article>
          );
        })}
      </div>
    </section>
  );
}
