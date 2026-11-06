import { test, expect } from '@playwright/test';
import { aboutT } from '../../src/lib/about-i18n';

for (const language of ['en', 'ar'] as const) {
  for (const width of [390, 1440]) {
    test(`About navigation, content and fit in ${language} at ${width}px`, async ({ page }) => {
      await page.setViewportSize({ width, height: 844 });
      await page.addInitScript(lang => {
        if (!localStorage.getItem('sada-language')) localStorage.setItem('sada-language', lang);
      }, language);
      const requests: string[] = [];
      page.on('request', req => {
        if (req.url().includes('/api/')) requests.push(req.url());
      });
      await page.goto('./');
      const caption = language === 'en'
        ? 'Four deterministic simulation agents; AI/RAG explanations are separate.'
        : 'أربعة وكلاء للمحاكاة الحتمية؛ شروح الذكاء الاصطناعي واسترجاع المعرفة منفصلة.';
      await expect(page.getByText(caption)).toBeVisible();
      await page.getByTestId('button-explore').click();
      await expect(page.getByRole('dialog').locator('ol li')).toHaveCount(4);
      await page.getByTestId('link-about-limits').click();
      await expect(page).toHaveURL(/\/about$/);
      const copy = aboutT[language];
      await expect(page.getByTestId('about-title')).toHaveText(copy.title);
      await expect(page.getByTestId('nav-6')).toHaveAttribute('aria-current', 'page');
      await expect(page.getByTestId('about-content')).toHaveAttribute('dir', language === 'ar' ? 'rtl' : 'ltr');
      await expect(page).toHaveTitle(copy.pageTitle);
      for (const [id, text] of [
        ['notice', copy.notice], ['scenario', copy.scenario],
        ['assumptions', copy.assumptions.join('')], ['ai', copy.ai.join('')],
        ['limits', copy.limits.join('')], ['privacy', copy.privacy],
      ]) {
        const section = page.getByTestId(`about-${id}`);
        if (['assumptions', 'ai', 'limits'].includes(id)) {
          for (const item of copy[id as 'assumptions' | 'ai' | 'limits']) await expect(section).toContainText(item);
        } else {
          await expect(section).toContainText(text);
        }
      }
      for (let i = 0; i < 4; i++) {
        await expect(page.getByTestId(`about-agent-${i}`)).toContainText(copy.agents[i][1]);
        await expect(page.getByTestId(`about-stage-${i}`)).toHaveText(copy.stages[i]);
      }
      for (let i = 0; i < 5; i++) await expect(page.getByTestId(`about-channel-${i}`)).toHaveText(copy.channels[i]);
      const overflow = await page.evaluate(() => ({
        page: document.documentElement.scrollWidth > innerWidth,
        content: Array.from(document.querySelectorAll('main section, main li, main dd, main h2'))
          .some(el => el.scrollWidth > el.clientWidth + 1),
      }));
      expect(overflow).toEqual({ page: false, content: false });

      // Language switching, persisted selection and direct reload use the real router/providers.
      const other = language === 'en' ? 'ar' : 'en';
      await page.getByTestId(`language-${other}`).click();
      await expect(page.getByTestId('about-title')).toHaveText(aboutT[other].title);
      await page.reload();
      await expect(page.getByTestId('about-title')).toHaveText(aboutT[other].title);
      await page.getByTestId(`language-${language}`).click();

      // The new sidebar item is keyboard reachable even in the mobile drawer.
      if (width < 1024) await page.getByTestId('button-menu').click();
      await page.getByTestId('nav-0').focus();
      await page.keyboard.press('Enter');
      await expect(page).toHaveURL(/\/$/);
      if (width < 1024) await page.getByTestId('button-menu').click();
      await page.getByTestId('nav-0').focus();
      for (let i = 0; i < 6; i++) await page.keyboard.press('Tab');
      await expect(page.getByTestId('nav-6')).toBeFocused();
      await page.keyboard.press('Enter');
      await expect(page.getByTestId('about-title')).toHaveText(copy.title);
      if (width < 1024) {
        await expect(page.locator('aside')).not.toBeInViewport();
        await page.getByTestId('button-menu').click();
        await expect(page.getByTestId('nav-6')).toBeInViewport();
      }
      expect(requests).toEqual([]);
    });
  }
}
