import { useId } from 'react';
import { Users, RadioTower, TrendingUp, AlertTriangle, Info, ArrowRight, ArrowLeft } from 'lucide-react';
import { metricChange, type EvaluatedPlan, type MetricKey } from '@/lib/results-model';
import type { ResultsT } from '@/lib/results-i18n';
import { fmtDelta, fmtMetric, fmtNum, unitLabel } from './format';

const icons = { reach: Users, effective: RadioTower, recovery: TrendingUp, critical: AlertTriangle };
const tone = { reach: 'text-primary', effective: 'text-[hsl(275_80%_72%)]', recovery: 'text-[hsl(160_75%_62%)]', critical: 'text-[hsl(350_80%_68%)]' };

export function KpiCard({ k, baseline, plan, t, rtl, index }: { k: MetricKey; baseline: EvaluatedPlan | null; plan: EvaluatedPlan | null; t: ResultsT; rtl: boolean; index: number }) {
  const tipId = useId();
  const Icon = icons[k];
  const b = baseline?.metrics[k] ?? null;
  const f = plan?.metrics[k] ?? null;
  const change = metricChange(b, f, k);
  const Arrow = rtl ? ArrowLeft : ArrowRight;
  const same = baseline && plan && baseline.id === plan.id;
  return (
    <article data-testid={`kpi-${k}`} className={`res-glass res-fade relative min-w-0 rounded-2xl p-5 hover:z-40 focus-within:z-40 ${k === 'critical' ? '' : index % 2 ? 'res-glow-purple' : 'res-glow-cyan'}`} style={{ animationDelay: `${index * 80}ms` }}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className={`grid h-11 w-11 place-items-center rounded-xl border border-white/10 bg-white/[.04] ${tone[k]}`}><Icon size={22} /></span>
          <h3 className="text-[15px] font-semibold leading-tight">{t.kpi[k]}</h3>
        </div>
        <span className="res-tip-host relative">
          <button type="button" aria-describedby={tipId} aria-label={t.kpi[k]} data-testid={`kpi-${k}-info`} className="rounded-md p-1 text-muted-foreground hover:text-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"><Info size={15} /></button>
          <span role="tooltip" id={tipId} className="res-tip res-glass rounded-xl p-3 text-xs leading-relaxed text-muted-foreground">
            {t.kpiHelp[k]}
            <span className="mt-2 block text-foreground/80">{t.baseline}: <bdi dir="ltr">{fmtMetric(b) ?? '—'}</bdi> {unitLabel(b, t)}</span>
            <span className="block text-foreground/80">{plan?.id ?? t.final}: <bdi dir="ltr">{fmtMetric(f) ?? '—'}</bdi> {unitLabel(f, t)}</span>
            {change && <span className="block text-foreground/80">{t.change}: <bdi dir="ltr">{fmtDelta(change, t)}</bdi>{change.relativePercent === null ? ` — ${t.noRelative}` : ` (${change.relativePercent > 0 ? '+' : ''}${fmtNum(change.relativePercent)}% ${t.relative})`}</span>}
          </span>
        </span>
      </div>
      <div className="mt-5 flex flex-wrap items-end justify-between gap-3">
        <div className="flex items-end gap-3">
          <div>
            <p className="font-mono text-2xl font-bold" data-testid={`kpi-${k}-baseline`}><bdi dir="ltr">{fmtMetric(b) ?? '—'}</bdi></p>
            <p className="text-[11px] text-muted-foreground">{t.baseline}</p>
          </div>
          {!same && <><Arrow size={18} className="mb-5 text-primary/70" />
          <div>
            <p className={`font-mono text-2xl font-bold ${f ? tone[k] : ''}`} data-testid={`kpi-${k}-final`}><bdi dir="ltr">{fmtMetric(f) ?? '—'}</bdi></p>
            <p className="text-[11px] text-muted-foreground">{t.final} <bdi dir="ltr">{plan?.id}</bdi></p>
          </div></>}
        </div>
        {change && !same && <span data-testid={`kpi-${k}-delta`} className={`res-delta ${change.improved || change.difference === 0 ? '' : 'res-delta-bad'}`}><bdi dir="ltr">{fmtDelta(change, t)}</bdi></span>}
      </div>
      <p className="mt-3 text-[11px] text-muted-foreground">{!b && !f ? t.notSupplied : (b ?? f)?.unit === 'residents' ? t.residents : '%'}</p>
    </article>
  );
}
