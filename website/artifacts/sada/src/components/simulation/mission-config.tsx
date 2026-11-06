import type { ReactNode } from 'react';
import type { SimulationDict } from '@/lib/simulation-i18n';

export function MissionConfig({ t, stage, channels }: { t: SimulationDict; stage: string; channels: string[] }) {
  const Row = ({ label, children, id }: { label: string; children: ReactNode; id: string }) => (
    <div className="flex items-center justify-between gap-3 border-b border-white/5 py-2.5 last:border-0">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div dir="ltr" data-testid={id} className="flex flex-wrap justify-end gap-1.5 font-mono text-[12px]">{children}</div>
    </div>
  );
  return (
    <section aria-labelledby="cfg-h" className="glass rounded-2xl p-5">
      <div className="mb-2 flex items-center justify-between">
        <h2 id="cfg-h" className="text-sm font-semibold">{t.config}</h2>
        <span className="h-1.5 w-1.5 rounded-full bg-primary shadow-[0_0_8px_hsl(182_90%_55%)]" />
      </div>
      <Row label={t.stage} id="config-stage"><span className="sim-chip sim-chip-on">{stage}</span></Row>
      <Row label={t.channels} id="config-channels">{channels.map((c) => <span key={c} className="sim-chip">{c}</span>)}</Row>
      <Row label={t.scenario} id="config-scenario"><span className="sim-chip">AL_WADI_FLASH_FLOOD</span></Row>
      <Row label={t.population} id="config-population"><span className="text-foreground">1,000</span></Row>
      <Row label={t.zones} id="config-zones">{['A', 'B', 'C'].map((z) => <span key={z} className="sim-chip w-7 justify-center">{z}</span>)}</Row>
      <p className="mt-2 text-[11px] text-muted-foreground/80">{t.fromPlanning}</p>
    </section>
  );
}
