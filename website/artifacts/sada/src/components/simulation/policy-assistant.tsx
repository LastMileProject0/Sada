import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useLanguage } from '@/lib/i18n';
import { askPolicy, type PolicyResponse } from '@/lib/policy-assistant';

const copy = {
  en: {
    title: 'AI Policy Assistant', note: 'Separate from deterministic results. Not legal certification.',
    label: 'Policy or accessibility question', placeholder: 'What does CAP say about the instruction field?',
    privacy: 'Do not enter personal or confidential information. Questions and public excerpts are sent to OpenRouter (Qwen2.5 7B). SADA does not save questions. Provider privacy policies apply.',
    submit: 'Ask assistant', busy: 'Retrieving evidence and checking the model…',
    answered: 'Evidence-grounded AI explanation',
    review: 'Insufficient Information — Review Required',
    model: 'Model unavailable. No AI explanation was generated.',
    limited: 'Request limit reached. Wait a minute before trying again.',
    unavailable: 'Policy service is busy or unavailable. Please try again later.',
    failed: 'The response could not be verified. Please try again.',
    evidence: 'Retrieved source excerpts — not AI-generated answers',
    citations: 'AI citations', caveat: 'Citations are structurally checked, not proof of legal or semantic correctness. Human review is required.',
    empty: 'No relevant excerpts found in the five-source knowledge base.',
    source: 'Official source', page: 'PDF page',
  },
  ar: {
    title: 'مساعد السياسات بالذكاء الاصطناعي', note: 'منفصل عن النتائج الحتمية. ليس شهادة امتثال قانوني.',
    label: 'سؤال عن السياسات أو الإتاحة', placeholder: 'ماذا يقول معيار CAP عن حقل التعليمات؟',
    privacy: 'لا تُدخل معلومات شخصية أو سرية. تُرسل الأسئلة والمقتطفات العامة إلى OpenRouter ‏(Qwen2.5 7B). لا يحفظ SADA الأسئلة. تسري سياسات خصوصية المزوّد.',
    submit: 'اسأل المساعد', busy: 'جارٍ استرجاع الأدلة والتحقق من النموذج…',
    answered: 'شرح بالذكاء الاصطناعي مستند إلى الأدلة',
    review: 'معلومات غير كافية — تتطلب المراجعة',
    model: 'النموذج غير متاح. لم يُولَّد شرح بالذكاء الاصطناعي.',
    limited: 'تم بلوغ حد الطلبات. انتظر دقيقة قبل المحاولة مجدداً.',
    unavailable: 'خدمة السياسات مشغولة أو غير متاحة. حاول لاحقاً.',
    failed: 'تعذر التحقق من الاستجابة. حاول مجدداً.',
    evidence: 'مقتطفات المصادر المسترجعة — ليست إجابات مولَّدة بالذكاء الاصطناعي',
    citations: 'استشهادات الشرح', caveat: 'تُفحص بنية الاستشهادات، لكنها لا تثبت الصحة القانونية أو الدلالية. المراجعة البشرية مطلوبة.',
    empty: 'لم تُعثر على مقتطفات ذات صلة في قاعدة المعرفة ذات المصادر الخمسة.',
    source: 'المصدر الرسمي', page: 'صفحة PDF',
  },
};

export function PolicyAssistant() {
  const { language, dir } = useLanguage();
  const t = copy[language];
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState<PolicyResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<keyof typeof t | null>(null);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!question.trim() || busy) return;
    const request = new AbortController();
    controller.current = request;
    setBusy(true); setResponse(null); setError(null);
    const timeout = window.setTimeout(() => request.abort(), 190_000);
    try {
      setResponse(await askPolicy(question.trim(), request.signal));
    } catch (failure) {
      if (!request.signal.aborted) {
        const key = failure instanceof Error ? failure.message : '';
        setError(key === 'limited' ? 'limited' : key === 'unavailable' ? 'unavailable' : 'failed');
      } else setError('unavailable');
    } finally {
      window.clearTimeout(timeout);
      if (controller.current === request) setBusy(false);
    }
  }

  const explanation = response?.explanation;
  const answered = explanation?.status === 'Answered';
  return (
    <div dir={dir} className="mt-4 border-t border-white/10 pt-4" data-testid="policy-assistant">
      <h4 className="text-sm font-semibold text-primary">{t.title}</h4>
      <p className="mt-1 text-xs text-muted-foreground">{t.note}</p>
      <form onSubmit={submit} className="mt-3 space-y-2">
        <label htmlFor="policy-question" className="block text-xs">{t.label}</label>
        <textarea id="policy-question" data-testid="policy-question" rows={3} maxLength={1200}
          required value={question} disabled={busy} placeholder={t.placeholder}
          onChange={event => setQuestion(event.target.value)}
          className="w-full resize-y rounded-xl border border-white/10 bg-white/[.03] p-3 text-xs outline-none focus:border-primary" />
        <p className="text-[11px] text-muted-foreground">{t.privacy}</p>
        <button type="submit" disabled={busy || !question.trim()} data-testid="policy-submit"
          className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-2 text-xs text-primary disabled:opacity-40">
          {busy ? t.busy : t.submit}
        </button>
      </form>
      <div aria-live="polite" aria-busy={busy} className="mt-3 space-y-3 text-xs" data-testid="policy-response">
        {error && <p role="alert">{t[error]}</p>}
        {explanation && <>
          <p className="font-semibold" data-testid="policy-status">
            {answered ? t.answered : explanation.status === 'ModelUnavailable' ? t.model : t.review}
          </p>
          {answered && <>
            <p dir="auto" className="whitespace-pre-wrap leading-relaxed">{explanation.answer}</p>
            <p className="text-muted-foreground">{explanation.model_id}</p>
            <p className="font-semibold">{t.citations}</p>
            <ul>{explanation.citations.map(c => <li key={c.passage_id}>
              <a href={c.official_url} target="_blank" rel="noopener noreferrer" className="text-primary underline">
                {c.passage_id} — {c.section}
              </a>
            </li>)}</ul>
            <p className="text-muted-foreground">{t.caveat}</p>
          </>}
          <h5 className="font-semibold">{t.evidence}</h5>
          {!response?.retrieval.evidence_items.length && <p>{t.empty}</p>}
          {response?.retrieval.evidence_items.map(e => <blockquote key={e.evidence_id}
            className="space-y-1 rounded-xl border border-white/10 p-3" data-testid="policy-evidence">
            <p dir="auto">{e.text}</p>
            <p dir="auto" className="text-muted-foreground">{e.evidence_id} — {e.source_title} — {e.section}
              {e.pdf_page != null && ` — ${t.page} ${e.pdf_page}`}</p>
            <a href={e.official_url} target="_blank" rel="noopener noreferrer" className="text-primary underline">{t.source}</a>
          </blockquote>)}
        </>}
      </div>
    </div>
  );
}
