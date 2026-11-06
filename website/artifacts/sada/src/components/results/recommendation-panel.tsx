import { Award, ShieldCheck } from 'lucide-react';
import type { EvaluationResult } from '@/lib/results-model';
import type { ResultsT } from '@/lib/results-i18n';

type Loc = { ar: string | null; en: string | null };

export function RecommendationPanel({ data, lang, t }: { data: EvaluationResult; lang: 'ar' | 'en'; t: ResultsT }) {
  const rec = data.recommendedPlanId;
  const ex = data.explanation;
  const pick = (l: Loc | null | undefined) => l?.[lang] ?? null;
  const list = (items: Loc[]) => items.map(pick).filter((s): s is string => !!s);
  const blocks = ex ? [
    { h: t.why, items: [pick(ex.reason)].filter((s): s is string => !!s) },
    { h: t.improvements, items: list(ex.improvements) },
    { h: t.accConsider, items: list(ex.accessibility) },
    { h: t.unresolved, items: [pick(ex.unresolved)].filter((s): s is string => !!s) },
    { h: t.tradeoffs, items: list(ex.tradeoffs) },
    { h: t.limitations, items: list(ex.limitations) },
  ].filter((b) => b.items.length) : [];
  return (
    <section className="res-glass res-glow-cyan relative overflow-hidden rounded-2xl p-6 md:p-8" aria-labelledby="rec-h" data-testid="panel-recommendation">
      <div className="res-scan pointer-events-none absolute inset-x-0 top-0 h-px" />
      <div className="flex flex-col gap-6 md:flex-row">
        <div className="flex shrink-0 items-center gap-4 md:w-64 md:flex-col md:items-start">
          <span className="grid h-14 w-14 place-items-center rounded-2xl border border-primary/40 bg-primary/10 text-primary"><Award size={28} /></span>
          <div>
            <h2 id="rec-h" className="text-xl font-semibold">{t.recTitle}</h2>
            <p className="mt-1 text-xs text-muted-foreground">{t.recPlan}</p>
            <p className="mt-1 font-mono text-2xl font-bold text-[hsl(275_80%_74%)]" data-testid="text-recommended-plan">{rec ?? '—'}</p>
            {rec && <p className="text-xs text-muted-foreground">{t.planNames[rec]}</p>}
          </div>
        </div>
        <div className="flex-1 border-white/10 md:border-s md:ps-6">
          {!rec && <p className="text-sm text-muted-foreground">{t.noRecommendation}</p>}
          {blocks.length ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {blocks.map((b) => <div key={b.h}><h3 className="text-xs font-medium uppercase tracking-wider text-primary">{b.h}</h3><ul className="mt-1.5 space-y-1 text-sm leading-relaxed">{b.items.map((s, i) => <li key={i}>{s}</li>)}</ul></div>)}
              <p className="col-span-full flex items-center gap-1.5 text-[11px] text-muted-foreground"><ShieldCheck size={12} />{ex?.source === 'rag' ? t.sourceRag : t.sourceBackend}</p>
            </div>
          ) : <p className="rounded-xl border border-dashed border-white/10 p-4 text-sm text-muted-foreground" data-testid="text-explanation-pending">{t.explPending}</p>}
        </div>
      </div>
    </section>
  );
}
