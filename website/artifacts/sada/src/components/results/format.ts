import type { ResultMetric } from '@/lib/results-model';
import type { ResultsT } from '@/lib/results-i18n';

export const fmtNum = (n: number) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(n);

export function fmtMetric(m: ResultMetric | null | undefined) {
  if (!m) return null;
  return m.unit === 'percent' ? `${fmtNum(m.value)}%` : fmtNum(m.value);
}

export function unitLabel(m: ResultMetric | null | undefined, t: ResultsT) {
  if (!m) return '';
  return m.unit === 'residents' ? t.residents : '';
}

export function fmtDelta(d: { difference: number; unit: 'pp' | 'residents' }, t: ResultsT) {
  const sign = d.difference > 0 ? '+' : d.difference < 0 ? '−' : '±';
  return `${sign}${fmtNum(Math.abs(d.difference))} ${d.unit === 'pp' ? t.pp : t.residents}`;
}
