import { describe, expect, it } from 'vitest';
import { searchDestination, searchPages } from './site-search';

describe('bounded bilingual public page search', () => {
  it('indexes only the seven actual navigation destinations', () => {
    expect(searchPages('', 'en').map(r => r.path)).toEqual([
      '/', '/planning', '/simulation', '/results', '/readiness', '/reports', '/about',
    ]);
  });
  it.each([
    ['planning', '/planning'], ['التَّخْطِيط', '/planning'],
    ['results', '/results'], ['النتائج', '/results'],
    ['الجاهزية', '/readiness'], ['resilience', '/readiness'],
    ['PDF', '/reports'], ['تقرير', '/reports'], ['agents', '/simulation'], ['limits', '/about'], ['حدوده', '/about'], ['Qwen', '/about'],
    ['About Limits', '/about'], ['عن صدى', '/about'],
  ])('matches %s to %s without external queries', (query, path) => {
    for (const language of ['en', 'ar'] as const) {
      expect(searchPages(query, language).some(r => r.path === path)).toBe(true);
    }
  });
  it('supports multiple terms, empty results and inert hostile input', () => {
    expect(searchPages('effective coverage', 'en').map(r => r.path)).toEqual(['/results']);
    expect(searchPages('no-matching-private-resident-xyz', 'ar')).toEqual([]);
    expect(searchPages('<script>alert(1)</script>', 'en')).toEqual([]);
  });
  it('keeps the exact evaluation selector only on aggregate-result destinations', () => {
    for (const path of ['/results', '/reports', '/readiness']) {
      expect(searchDestination(path, 'id&another=private')).toBe(`${path}?evaluationId=id%26another%3Dprivate`);
    }
    expect(searchDestination('/planning', 'id')).toBe('/planning');
    expect(searchDestination('/results', null)).toBe('/results');
  });
});
