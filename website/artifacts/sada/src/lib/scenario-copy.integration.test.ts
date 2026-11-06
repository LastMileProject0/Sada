import { describe, expect, it } from 'vitest';
import { translations } from './i18n';
import { planningT } from './planning-i18n';
import { simulationT } from './simulation-i18n';
import { readinessT } from './readiness-i18n';
import { aboutT } from './about-i18n';
import { ABOUT_CHANNELS } from './about-content';

describe.each(['en', 'ar'] as const)('evidence-bound scenario copy in %s', language => {
  it('states the exact synthetic population and preserves the approved agent caption', () => {
    const shared = translations[language];
    expect(shared.steps[1]).toContain('1,000');
    expect(shared.steps[1]).not.toMatch(/around|نحو/);
    expect(shared.agents).toBe(language === 'en'
      ? 'Four deterministic simulation agents; AI/RAG explanations are separate.'
      : 'أربعة وكلاء للمحاكاة الحتمية؛ شروح الذكاء الاصطناعي واسترجاع المعرفة منفصلة.');
    expect(shared.channels).toHaveLength(ABOUT_CHANNELS.length);
  });
  it('matches the verified cumulative EV03 boundary without an actual-sharing claim', () => {
    const stage = planningT[language].stages['T+06'];
    expect(stage).toContain('EV01');
    expect(stage).toContain('EV02');
    expect(stage).toContain('EV03');
    expect(stage).toContain(language === 'en' ? 'excluded hypothetical' : 'افتراضي مستبعد');
    expect(stage).toContain(language === 'en' ? 'does not mean external sharing occurred' : 'لا تعني حدوث مشاركة خارجية');
    expect(stage).toBe(readinessT[language].stageContext['T+06']);
    expect(aboutT[language].stages[3]).toContain(language === 'en' ? 'excluded hypothetical' : 'افتراضياً مستبعداً');
    // Availability copies must not make a disconnected-engine claim.
    expect(planningT[language].pendingBody).not.toMatch(/not connected|غير متصل/);
    expect(simulationT[language].pendingBody).not.toMatch(/not connected|لم يُربط/);
  });
  it('does not claim working modules are unavailable', () => {
    for (const copy of [translations[language].planningNote, translations[language].moduleNote,
      translations[language].comingSoon, planningT[language].comingSoon, simulationT[language].soon]) {
      expect(copy).not.toMatch(/coming soon|later build|only.*available|not part|قريب|إصدار لاحق|فقط متاحت|ليست جزءاً/);
    }
  });
});
