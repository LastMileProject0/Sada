import { useId, useState } from 'react';
import { Radio, MessageSquare, Smartphone, PhoneCall, Siren, MonitorSmartphone } from 'lucide-react';
import { CHANNEL_IDS } from '@/lib/planning-state';
import type { ChannelPerformance, EvaluatedPlan } from '@/lib/results-model';
import type { ResultsT } from '@/lib/results-i18n';
import { fmtNum } from './format';

const icons = { CH01: MessageSquare, CH02: Smartphone, CH03: PhoneCall, CH04: Siren, CH05: MonitorSmartphone };
const states = ['selectedAttempts', 'delivered', 'delayed', 'failed', 'unavailable'] as const;

function Row({ id, ch, t }: { id: typeof CHANNEL_IDS[number]; ch: ChannelPerformance | undefined; t: ResultsT }) {
  const tip = useId();
  const Icon = icons[id];
  const attempts = ch?.selectedAttempts ?? null;
  return (
    <li className="res-tip-host relative rounded-xl border border-white/10 bg-white/[.03] p-3" data-testid={`channel-row-${id}`}>
      <div tabIndex={0} aria-describedby={tip} className="flex items-center gap-3 rounded-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
        <Icon size={18} className="shrink-0 text-primary" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium"><bdi dir="ltr" className="font-mono text-xs text-muted-foreground">{id}</bdi> · {t.chNames[id]}</p>
          {id === 'CH04' && <p className="text-[11px] text-[hsl(40_90%_70%)]">{t.sirenNote}</p>}
          {id === 'CH01' && <p className="text-[11px] text-muted-foreground">{t.smsNote}</p>}
        </div>
        <span className="font-mono text-xs">{ch?.delivered == null ? '—' : fmtNum(ch.delivered)}</span>
      </div>
      {ch && attempts !== null && attempts > 0 && ch.delivered !== null && (
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/[.06]"><div className="res-bar h-full rounded-full bg-gradient-to-r from-[hsl(182_85%_50%)] to-[hsl(275_80%_66%)]" style={{ width: `${Math.min(100, (ch.delivered / attempts) * 100)}%` }} /></div>
      )}
      <span role="tooltip" id={tip} className="res-tip res-glass rounded-xl p-3 text-xs">
        {states.map((s) => <span key={s} className="flex justify-between gap-4"><span className="text-muted-foreground">{t.states[s]}</span><span className="font-mono">{ch?.[s] == null ? t.unavailable : fmtNum(ch[s] as number)}</span></span>)}
      </span>
    </li>
  );
}

export function ChannelPanel({ baseline, plan, t }: { baseline: EvaluatedPlan | null; plan: EvaluatedPlan | null; t: ResultsT }) {
  const [view, setView] = useState<'before' | 'after'>(plan?.channels.length ? 'after' : 'before');
  const hasBefore = !!baseline?.channels.length, hasAfter = !!plan?.channels.length;
  const any = hasBefore || hasAfter;
  const shown = view === 'before' ? baseline : plan;
  return (
    <section className="res-glass rounded-2xl p-5" aria-labelledby="ch-h" data-testid="panel-channels">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3"><Radio className="text-primary" size={22} />
          <div><h2 id="ch-h" className="text-lg font-semibold">{t.chTitle}</h2><p className="text-xs text-muted-foreground">{t.chSub}</p></div></div>
        <div role="group" className="flex rounded-lg border border-white/10 p-0.5 text-xs" title={any ? undefined : t.chNone}>
          {(['before', 'after'] as const).map((v) => {
            const enabled = v === 'before' ? hasBefore : hasAfter;
            return <button key={v} data-testid={`channel-${v}`} disabled={!enabled} aria-pressed={view === v} onClick={() => setView(v)}
              className={`rounded-md px-3 py-1 transition disabled:cursor-not-allowed disabled:opacity-40 ${view === v && enabled ? 'bg-primary/20 text-foreground' : 'text-muted-foreground'}`}>
              {v === 'before' ? t.before : t.after} <bdi dir="ltr" className="font-mono">{v === 'before' ? 'P0' : plan?.id}</bdi></button>;
          })}
        </div>
      </div>
      {!any && <p className="mb-3 rounded-xl border border-dashed border-white/10 p-3 text-xs text-muted-foreground" data-testid="text-channels-none">{t.chNone}</p>}
      <ul className="space-y-2">
        {CHANNEL_IDS.map((id) => <Row key={id} id={id} ch={shown?.channels.find((c) => c.id === id)} t={t} />)}
      </ul>
    </section>
  );
}
