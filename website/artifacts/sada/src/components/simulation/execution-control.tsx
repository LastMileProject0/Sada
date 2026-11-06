import { Play, RotateCcw, ArrowLeft, ArrowRight, Lock, CircleAlert, Hourglass } from 'lucide-react';
import type { SimulationDict } from '@/lib/simulation-i18n';
import type { ExecutionStatus } from '@/lib/simulation';

type Status = ExecutionStatus;

export function ExecutionControl({ t, status, pending, error, resultId, onStart, onReset, onBack, onResults, rtl }: {
  t: SimulationDict; status: Status; pending: boolean; error: string | null; resultId: string | null;
  onStart: () => void; onReset: () => void; onBack: () => void; onResults: () => void; rtl: boolean;
}) {
  const canResults = status === 'completed' && !!resultId;
  const Fwd = rtl ? ArrowLeft : ArrowRight, Back = rtl ? ArrowRight : ArrowLeft;
  const tone = status === 'error' ? 'hsl(352 85% 62%)' : status === 'completed' ? 'hsl(160 80% 55%)' : status === 'running' ? 'hsl(182 90% 60%)' : 'hsl(220 20% 65%)';
  return (
    <section aria-labelledby="ctl-h" className="glass rounded-2xl p-5">
      <h2 id="ctl-h" className="text-sm font-semibold">{t.control}</h2>
      <div className="mt-3 flex items-center justify-between rounded-xl border border-white/5 bg-white/[.02] px-3.5 py-2.5">
        <span className="text-xs text-muted-foreground">{t.status}</span>
        <span data-testid="simulation-status" role="status" aria-live="polite" className="flex items-center gap-2 text-sm font-medium" style={{ color: tone }}>
          <span className={`h-2 w-2 rounded-full ${status === 'running' ? 'animate-pulse' : ''}`} style={{ background: tone, boxShadow: `0 0 8px ${tone}` }} />
          {t.statuses[status]}
        </span>
      </div>
      {pending ? (
        <div role="status" data-testid="integration-pending" className="mt-3 flex gap-3 rounded-xl border border-[hsl(42_95%_60%/.3)] bg-[hsl(42_95%_60%/.06)] p-3.5">
          <Hourglass size={16} className="mt-0.5 shrink-0 text-[hsl(42_95%_65%)]" />
          <div><p className="text-[13px] font-medium text-[hsl(42_95%_75%)]">{t.pendingTitle}</p><p className="mt-1 text-xs leading-relaxed text-muted-foreground">{t.pendingBody}</p></div>
        </div>
      ) : status === 'error' ? (
        <div className="mt-3 flex gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-3.5">
          <CircleAlert size={16} className="mt-0.5 shrink-0 text-destructive" />
          <div><p className="text-[13px] font-medium">{t.errorTitle}</p>{error && <p className="mt-1 text-xs text-muted-foreground">{t.errorBody}</p>}</div>
        </div>
      ) : <p className="mt-3 text-xs leading-relaxed text-muted-foreground">{status === 'restoring' ? t.restoringNote : status === 'running' ? t.runningNote : status === 'completed' ? t.completedNote : t.idle}</p>}
      <div className="mt-4 grid grid-cols-[1fr_auto] gap-2">
        <button data-testid="simulation-start" onClick={onStart} disabled={status === 'running' || status === 'restoring'}
          className="sim-cta flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold disabled:opacity-50">
          <Play size={16} className="rtl:-scale-x-100" />{t.start}
        </button>
        <button data-testid="simulation-reset" onClick={onReset} aria-label={t.reset} title={t.reset}
          className="grid place-items-center rounded-xl border border-white/10 px-3.5 text-muted-foreground transition hover:border-primary/40 hover:text-primary"><RotateCcw size={16} /></button>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2">
        <button data-testid="back-planning" onClick={onBack} className="flex items-center justify-center gap-1.5 rounded-xl border border-white/10 px-3 py-2.5 text-xs transition hover:bg-white/5">
          <Back size={14} />{t.back}
        </button>
        <button data-testid="results-navigation" onClick={onResults} disabled={!canResults} aria-disabled={!canResults} title={canResults ? undefined : t.resultsLocked}
          className="flex items-center justify-center gap-1.5 rounded-xl border border-white/10 px-3 py-2.5 text-xs transition enabled:hover:border-primary/40 disabled:cursor-not-allowed disabled:opacity-45">
          {canResults ? <Fwd size={14} /> : <Lock size={13} />}{t.results}
        </button>
      </div>
      {!canResults && <p className="mt-2 text-center text-[11px] text-muted-foreground/70">{t.resultsLocked}</p>}
    </section>
  );
}
