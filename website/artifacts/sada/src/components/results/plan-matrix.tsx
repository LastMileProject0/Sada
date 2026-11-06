import { Layers, BadgeCheck } from 'lucide-react';
import { metricKeys, type EvaluatedPlan, type EvaluationResult } from '@/lib/results-model';
import type { ResultsT } from '@/lib/results-i18n';
import { fmtMetric } from './format';

export function PlanMatrix({ data, selectedId, onSelect, t }: { data: EvaluationResult; selectedId: string; onSelect: (id: EvaluatedPlan['id']) => void; t: ResultsT }) {
  const plans = data.plans;
  return (
    <section className="res-glass min-w-0 rounded-2xl p-5 md:p-6" aria-labelledby="plans-h">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Layers className="text-primary" size={22} />
          <div><h2 id="plans-h" className="text-lg font-semibold">{t.plansTitle}</h2><p className="text-xs text-muted-foreground">{t.plansSub}</p></div>
        </div>
        <div role="radiogroup" aria-label={t.selectPlan} className="flex flex-wrap gap-2">
          {plans.map((p) => (
            <button key={p.id} role="radio" aria-checked={p.id === selectedId} data-testid={`plan-${p.id}`} onClick={() => onSelect(p.id)}
              className={`rounded-lg border px-3 py-1.5 font-mono text-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary ${p.id === selectedId ? 'border-[hsl(275_80%_66%)] bg-[hsl(275_70%_50%/.2)] text-foreground' : 'border-white/10 text-muted-foreground hover:border-primary/50 hover:text-foreground'}`}>
              {p.id}
            </button>
          ))}
        </div>
      </div>
      <div className="relative min-w-0 max-w-full overflow-x-auto" tabIndex={0} role="region" aria-label={t.plansTitle}>
        <table className={`w-full border-separate border-spacing-x-1.5 border-spacing-y-1 text-sm ${plans.length > 2 ? 'min-w-[560px]' : 'min-w-0 table-fixed [overflow-wrap:anywhere]'}`}>
          <thead>
            <tr>
              <th scope="col" className="w-[40%] px-2 py-2 text-start text-xs font-medium text-muted-foreground sm:px-3">{t.metric}</th>
              {plans.map((p) => {
                const sel = p.id === selectedId, rec = p.id === data.recommendedPlanId;
                return (
                  <th key={p.id} scope="col" className={`rounded-t-xl px-2 py-2 text-center align-bottom sm:px-3 ${sel ? 'bg-[hsl(275_70%_45%/.22)] shadow-[0_0_24px_-8px_hsl(275_85%_62%)]' : 'bg-white/[.03]'}`}>
                    {rec && <span title={t.recommended} aria-label={t.recommended} data-testid={`badge-recommended-${p.id}`} className="mb-1.5 inline-flex max-w-full items-center gap-1 rounded-full border border-[hsl(160_70%_55%/.5)] bg-[hsl(160_60%_30%/.2)] px-2 py-0.5 text-[10px] text-[hsl(160_75%_70%)]"><BadgeCheck size={11} className="shrink-0" /><span className="sr-only sm:not-sr-only">{t.recommended}</span></span>}
                    <span className="block font-mono text-base">{p.id}</span>
                    <span className="block text-[11px] font-normal text-muted-foreground">{t.planNames[p.id]}</span>
                    {sel && <span className="mt-1 block text-[10px] font-medium text-[hsl(275_80%_78%)]">{t.selected}</span>}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {metricKeys.map((k) => (
              <tr key={k}>
                <th scope="row" className="rounded-s-lg bg-white/[.02] px-3 py-3 text-start text-[13px] font-medium">{t.kpi[k]}</th>
                {plans.map((p) => {
                  const v = fmtMetric(p.metrics[k]);
                  const sel = p.id === selectedId;
                  return (
                    <td key={p.id} data-testid={`cell-${p.id}-${k}`} className={`px-3 py-3 text-center font-mono transition ${sel ? 'bg-[hsl(275_70%_45%/.14)] font-bold text-foreground' : 'bg-white/[.02] text-foreground/80'}`}>
                      {v ? <bdi dir="ltr">{v}</bdi> : <span aria-label={t.unavailable} title={t.unavailable} className="text-muted-foreground">—</span>}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!data.recommendedPlanId && <p className="mt-3 text-xs text-muted-foreground">{t.noRecommendation}</p>}
    </section>
  );
}
