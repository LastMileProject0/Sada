import { Accessibility } from 'lucide-react';
import { groupIds, groupReviewCount, type EvaluatedPlan } from '@/lib/results-model';
import type { ResultsT } from '@/lib/results-i18n';
import { fmtNum } from './format';

export function AccessibilityPanel({ baseline, plan, population, t }: { baseline: EvaluatedPlan | null; plan: EvaluatedPlan | null; population: number; t: ResultsT }) {
  const before = baseline?.accessibility?.uniqueResidentsWithGaps ?? null;
  const after = plan?.accessibility?.uniqueResidentsWithGaps ?? null;
  const none = !baseline?.accessibility && !plan?.accessibility;
  const rows = [
    { key: 'before', label: t.beforeGaps, v: before, cls: 'from-[hsl(182_85%_50%)] to-[hsl(200_85%_60%)]' },
    { key: 'after', label: `${t.afterGaps} · ${plan?.id ?? ''}`, v: after, cls: 'from-[hsl(250_80%_62%)] to-[hsl(285_80%_68%)]' },
  ];
  return (
    <section className="res-glass rounded-2xl p-5" aria-labelledby="acc-h" data-testid="panel-accessibility">
      <div className="mb-4 flex items-center gap-3"><Accessibility className="text-primary" size={22} />
        <div><h2 id="acc-h" className="text-lg font-semibold">{t.accTitle}</h2><p className="text-xs text-muted-foreground">{t.accSub}</p></div></div>
      {none && <p className="mb-4 rounded-xl border border-dashed border-white/10 p-4 text-sm text-muted-foreground" data-testid="text-accessibility-none">{t.accNone}</p>}
          <div className="space-y-3">
            {rows.map((r) => (
              <div key={r.key} data-testid={`acc-${r.key}`}>
                <div className="mb-1 flex justify-between text-xs"><span>{r.label}</span><span className="font-mono">{r.v === null ? '—' : `${fmtNum(r.v)} ${t.residents}`}</span></div>
                {r.v !== null && <div className="h-2 overflow-hidden rounded-full bg-white/[.06]">
                  <div className={`res-bar h-full rounded-full bg-gradient-to-r ${r.cls}`} style={{ width: `${(r.v / population) * 100}%` }} />
                </div>}
              </div>
            ))}
          </div>
          <h3 className="mb-2 mt-5 text-xs font-medium uppercase tracking-wider text-muted-foreground">{t.groupsReview}</h3>
          <dl className="grid grid-cols-2 gap-2">
            {groupIds.map((g) => {
              const b = groupReviewCount(baseline, g), a = groupReviewCount(plan, g);
              return (
                <div key={g} className="rounded-xl border border-white/10 bg-white/[.03] p-2.5" data-testid={`acc-group-${g}`}>
                  <dt className="text-[11px] text-muted-foreground">{t.groups[g]}</dt>
                  <dd className="mt-1 font-mono text-sm" dir="ltr">{b === null ? '—' : fmtNum(b)} → {a === null ? '—' : fmtNum(a)}</dd>
                </div>
              );
            })}
          </dl>
    </section>
  );
}
