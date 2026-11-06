import { createContext, useContext, useLayoutEffect, useState, type ReactNode } from 'react';

export const translations = {
  en: {
    nav: ['Home', 'Planning', 'Testing & Simulation', 'Compare Plans', 'Resilience', 'Report Center', 'About & Limits'],
    aboutLink: 'Read SADA’s purpose, assumptions & limits',
    features: ['Planning & Testing', 'Accessibility First', 'Compare Plans', 'Resilience'],
    descriptions: ['Design, test, and validate emergency plans.', 'Inclusive alerts and guidance for everyone.', 'Compare alternatives and choose the best fit.', 'More prepared, more resilient communities.'],
    metrics: ['Simulated Residents', 'Warning Channels', 'Simulation agents', 'Accessibility First'],
    accessibility: 'A11y',
    heading: 'A pre-event emergency planning platform.',
    start: 'Start Planning', explore: 'Explore How SADA Works', how: 'How SADA Works',
    search: 'Search', language: 'Language', arabic: 'Arabic', english: 'English',
    menu: 'Open menu', close: 'Close', account: 'Account',
    illustrative: 'Illustrative scenario figures', preview: 'Scenario Preview', demo: 'Demo',
    previewLabel: 'Illustrative preview', curve: 'Illustrative warning-reach curve',
    channels: ['SMS', 'Mobile App', 'Automated Voice Call', 'Public Sirens', 'Digital Signage'],
    agents: 'Four deterministic simulation agents; AI/RAG explanations are separate.',
    samples: 'Sample values only.',
    planningIntro: 'Planning in SADA uses one fixed synthetic scenario. Choose a cumulative snapshot and enabled warning channels.',
    planningNote: 'Open Planning to configure an evaluation, then request a deterministic run in Testing & Simulation. This information panel does not start an evaluation.',
    steps: ['Design an emergency plan before an event happens.', 'Test it against a fixed synthetic population of exactly 1,000 residents with diverse needs.', 'Measure reach across 5 warning channels, with accessibility treated as a first requirement.', 'Compare alternatives and strengthen community resilience.'],
    concept: 'Concept overview. Figures are illustrative, not live data.',
    moduleNote: 'Use the sidebar to open the available planning, simulation, comparison, readiness and reporting pages.',
    comingSoon: 'Use the sidebar to open the available pages. This information panel does not run an evaluation.',
    notifications: 'Notifications', noNotifications: 'No notifications. SADA does not send real alerts.',
    notFound: '404 Page Not Found', missingPage: 'Did you forget to add the page to the router?',
    error: 'Something went wrong', errorDescription: 'This part of the app hit an error. The rest of the app is still running.',
    retry: 'Try again', title: 'SADA — Emergency Intelligence',
  },
  ar: {
    nav: ['الرئيسية', 'التخطيط', 'الاختبار والمحاكاة', 'مقارنة الخطط', 'الجاهزية والمرونة', 'مركز التقارير', 'عن صدى وحدوده'],
    aboutLink: 'اقرأ عن هدف صدى وافتراضاته وحدوده',
    features: ['التخطيط والاختبار', 'إتاحة للجميع أولاً', 'مقارنة الخطط', 'المرونة والجاهزية'],
    descriptions: ['صمّم خطط الطوارئ وتحقق من جاهزيتها', 'تحذيرات وإرشادات للجميع دون استثناء', 'قارن البدائل واختر الأنسب لاحتياجاتك', 'مجتمعات أكثر استعداداً وقدرة على التعافي'],
    metrics: ['مقيم افتراضي', 'قنوات تحذير', 'وكلاء المحاكاة', 'الإتاحة أولاً'],
    accessibility: 'إتاحة',
    heading: 'منصة التخطيط المسبق للطوارئ',
    start: 'ابدأ التخطيط', explore: 'اعرف كيف يعمل صدى', how: 'كيف يعمل صدى',
    search: 'ابحث', language: 'اللغة', arabic: 'العربية', english: 'الإنجليزية',
    menu: 'فتح القائمة', close: 'إغلاق', account: 'الحساب',
    illustrative: 'أرقام توضيحية للسيناريو', preview: 'معاينة السيناريو', demo: 'نموذج توضيحي',
    previewLabel: 'معاينة توضيحية', curve: 'نموذج توضيحي لوصول التحذير',
    channels: ['الرسائل النصية', 'تطبيق الجوال', 'المكالمة الصوتية الآلية', 'صفارات الإنذار العامة', 'اللوحات الرقمية'],
    agents: 'أربعة وكلاء للمحاكاة الحتمية؛ شروح الذكاء الاصطناعي واسترجاع المعرفة منفصلة.',
    samples: 'قيم توضيحية فقط.',
    planningIntro: 'يستخدم التخطيط في صدى سيناريو افتراضياً واحداً ثابتاً. اختر لقطة تراكمية وقنوات التحذير المفعّلة.',
    planningNote: 'افتح التخطيط لإعداد تقييم، ثم اطلب تشغيل المحاكاة الحتمية في الاختبار والمحاكاة. لا تبدأ نافذة المعلومات هذه أي تقييم.',
    steps: ['صمّم خطة للطوارئ قبل وقوع الحدث.', 'اختبرها على مجتمع افتراضي ثابت يضم 1,000 مقيم بالضبط ذوي احتياجات متنوعة.', 'قِس الوصول عبر 5 قنوات تحذير، مع اعتبار الإتاحة للجميع متطلباً أساسياً.', 'قارن البدائل وعزّز مرونة المجتمع.'],
    concept: 'نظرة عامة على المفهوم. الأرقام توضيحية وليست بيانات مباشرة.',
    moduleNote: 'استخدم القائمة الجانبية لفتح صفحات التخطيط والمحاكاة والمقارنة والجاهزية والتقارير المتاحة.',
    comingSoon: 'استخدم القائمة الجانبية لفتح الصفحات المتاحة. لا تشغّل نافذة المعلومات هذه أي تقييم.',
    notifications: 'الإشعارات', noNotifications: 'لا توجد إشعارات. لا يرسل صدى تنبيهات حقيقية.',
    notFound: '404 الصفحة غير موجودة', missingPage: 'هل نسيت إضافة الصفحة إلى مسارات الموقع؟',
    error: 'حدث خطأ ما', errorDescription: 'حدث خطأ في هذا الجزء من التطبيق. بقية التطبيق لا تزال تعمل.',
    retry: 'حاول مجدداً', title: 'صدى — ذكاء الطوارئ',
  },
};

type Language = keyof typeof translations;
const LanguageContext = createContext<{
  language: Language;
  setLanguage: (language: Language) => void;
} | null>(null);
export const languageStorageKey = 'sada-language';

export function readLanguage(): Language {
  try {
    return localStorage.getItem(languageStorageKey) === 'en' ? 'en' : 'ar';
  } catch {
    return 'ar';
  }
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(readLanguage);
  useLayoutEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
    document.title = translations[language].title;
    try { localStorage.setItem(languageStorageKey, language); } catch { /* Storage may be blocked; switching still works. */ }
  }, [language]);
  return <LanguageContext.Provider value={{ language, setLanguage }}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error('LanguageProvider is required');
  return { ...context, t: translations[context.language], dir: context.language === 'ar' ? 'rtl' as const : 'ltr' as const };
}
