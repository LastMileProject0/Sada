import { translations } from './i18n';

export const searchCopy = {
  en: { label: 'Search pages', scope: 'Website pages only — not evaluations, residents or knowledge-base documents.',
    none: 'No matching pages.', hint: 'Try Planning, Results, reports or accessibility.', clear: 'Clear search', open: 'Open page search' },
  ar: { label: 'البحث في الصفحات', scope: 'صفحات الموقع فقط — لا يشمل التقييمات أو السكان أو وثائق قاعدة المعرفة.',
    none: 'لا توجد صفحات مطابقة.', hint: 'جرّب التخطيط أو النتائج أو التقارير أو الإتاحة.', clear: 'مسح البحث', open: 'فتح البحث في الصفحات' },
};

const destinations = [
  { path: '/', en: 'Home SADA overview', ar: 'الرئيسية صدى نظرة عامة' },
  { path: '/planning', en: 'Planning Studio scenario stage channels configuration', ar: 'استوديو التخطيط السيناريو المرحلة القنوات الإعدادات' },
  { path: '/simulation', en: 'Testing Simulation agents execution delivery risk policy accessibility recovery', ar: 'الاختبار المحاكاة الوكلاء التنفيذ التوصيل المخاطر السياسات الإتاحة التعافي' },
  { path: '/results', en: 'Results Dashboard compare plans reach effective coverage recovery accessibility', ar: 'لوحة النتائج مقارنة الخطط الوصول التغطية الفعالة التعافي الإتاحة' },
  { path: '/readiness', en: 'Readiness Resilience warning delivery accessibility connectivity', ar: 'الجاهزية المرونة تسليم التحذير الإتاحة الاتصال' },
  { path: '/reports', en: 'Report Center export download PDF HTML', ar: 'مركز التقارير تقرير التقييم تصدير تنزيل تحميل PDF HTML' },
  { path: '/about', en: 'About Limits scope purpose synthetic residents scenario channels deterministic agents AI Qwen RAG assumptions disclaimer', ar: 'عن صدى حدوده حول الحدود النطاق مقيمين افتراضيين الهدف الافتراضات صناعي حتمي السيناريو القنوات الذكاء الاصطناعي استرجاع المعرفة الوكلاء إخلاء المسؤولية' },
] as const;

function normalize(value: string) {
  return value.toLocaleLowerCase().normalize('NFKD')
    .replace(/[\u0300-\u036f\u064b-\u065f\u0670\u0640]/g, '')
    .replace(/[أإآٱ]/g, 'ا').replace(/ى/g, 'ي').replace(/\s+/g, ' ').trim();
}

/** Public, curated navigation only. Queries never leave this component or enter storage. */
export function searchPages(query: string, language: 'en' | 'ar') {
  const terms = normalize(query.slice(0, 128)).split(' ').filter(Boolean);
  return destinations.map((page, i) => ({
    path: page.path, title: translations[language].nav[i],
    indexed: normalize(`${page.en} ${page.ar} ${translations.en.nav[i]} ${translations.ar.nav[i]}`),
  })).filter(page => terms.every(term => page.indexed.includes(term)))
    .map(({ path, title }) => ({ path, title }));
}

export function searchDestination(path: string, evaluationId: string | null) {
  return evaluationId && ['/results', '/readiness', '/reports'].includes(path)
    ? `${path}?evaluationId=${encodeURIComponent(evaluationId)}` : path;
}
