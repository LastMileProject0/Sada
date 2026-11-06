import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { Header, Panel, Sidebar } from '@/components/shell';
import { useLanguage } from '@/lib/i18n';
import { aboutT } from '@/lib/about-i18n';
import { aboutT as detailsT, ABOUT_CHANNELS, ABOUT_SCENARIO_ID } from '@/lib/about-content';
import { readSavedEvaluationId } from '@/lib/evaluation-session';

// Mark identifiers without translating or rewriting their surrounding claims.
function IdentifierText({ children }: { children: string }) {
  return <>{children.split(/(AL_WADI_FLASH_FLOOD|T\+\d{2}|EV0[123]|CH0[1-5]|ReviewRequired|InsufficientInformation|ModelUnavailable|Qwen|RAG|CAP|P[0-3](?:–P[0-3])?|UAE-Alert)/g)
    .map((part, i) => i % 2 ? <bdi key={i} lang="en" dir="ltr">{part}</bdi> : part)}</>;
}

export default function About() {
  const { language, dir, t: shared } = useLanguage();
  const t = aboutT[language];
  const details = detailsT[language];
  const [, navigate] = useLocation();
  const [menu, setMenu] = useState(false);
  const [notifications, setNotifications] = useState(false);

  useEffect(() => {
    const previous = document.title;
    document.title = t.pageTitle;
    const undo = [
      ['name', 'description', t.description],
      ['property', 'og:title', t.pageTitle],
      ['property', 'og:description', t.description],
      ['property', 'og:type', 'website'],
    ].map(([attribute, key, content]) => {
      let meta = document.head.querySelector<HTMLMetaElement>(`meta[${attribute}="${key}"]`);
      const created = !meta;
      const oldContent = meta?.getAttribute('content');
      if (!meta) { meta = document.createElement('meta'); meta.setAttribute(attribute, key); document.head.appendChild(meta); }
      meta.content = content;
      return () => { if (created) meta.remove(); else if (oldContent != null) meta.content = oldContent; else meta.removeAttribute('content'); };
    });
    return () => { document.title = previous; undo.forEach(f => f()); };
  }, [t]);

  useEffect(() => {
    if (!menu) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setMenu(false); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [menu]);

  const onNav = (i: number) => {
    const path = ['/', '/planning', '/simulation', '/results'][i];
    if (!path) return;
    const id = i === 3 ? readSavedEvaluationId() : null;
    navigate(id ? `${path}?evaluationId=${encodeURIComponent(id)}` : path);
  };
  const sections = [
    { id: 'assumptions', title: t.assumptionsTitle, items: t.assumptions },
    { id: 'ai', title: t.aiTitle, items: t.ai },
    { id: 'limits', title: t.limitsTitle, items: t.limits },
  ];
  const panelClass = 'glass neon-border rounded-2xl p-5 md:p-7';

  return (
    <div dir="ltr" className="sada-home min-h-[100dvh] bg-background text-foreground">
      <Sidebar active={6} menu={menu} setMenu={setMenu} onNav={onNav} accessibleAbout />
      <div className="min-w-0 lg:pl-60">
        <Header setMenu={setMenu} onNotifications={() => setNotifications(true)} aboutMenuOpen={menu} />
        <main dir={dir} lang={language} data-testid="about-content" className="relative mx-auto min-w-0 max-w-5xl space-y-6 break-words px-4 pb-16 pt-8 md:px-8">
          <div data-testid="page-about">
            <h1 data-testid="about-title" className="text-3xl font-semibold"><span data-testid="text-about-title">{t.title}</span></h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">{t.intro}</p>
            <div className="mt-5 flex flex-wrap gap-3">
              <button data-testid="button-about-planning" onClick={() => onNav(1)} className="rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground">{details.ctaPlan}</button>
              <button data-testid="button-about-results" onClick={() => onNav(3)} className="rounded-xl border border-white/15 px-5 py-2.5 text-sm font-medium hover:border-primary/60">{details.ctaResults}</button>
            </div>
          </div>
          <nav aria-label={details.toc} className="flex flex-wrap gap-2">
            {[
              ['scenario', t.scenarioTitle], ['channels', t.channelsTitle], ['agents', t.agentsTitle],
              ['assumptions', t.assumptionsTitle], ['ai', t.aiTitle], ['limits', t.limitsTitle],
            ].map(([id, title]) => <a key={id} data-testid={`link-toc-${id}`} href={`#about-${id}`} className="rounded-full border border-white/10 px-3 py-1.5 text-xs hover:border-primary/50">{title}</a>)}
          </nav>
          <p data-testid="about-notice" className={`${panelClass} text-sm leading-7`}>{t.notice}</p>
          <section id="about-scenario" data-testid="about-scenario" aria-labelledby="about-scenario-title" className={panelClass}>
            <h2 id="about-scenario-title" className="text-xl font-semibold">{t.scenarioTitle}</h2>
            <p dir="ltr" lang="en" data-testid="text-scenario-id" className="mt-3 font-mono text-xs text-primary">{ABOUT_SCENARIO_ID}</p>
            <p className="mt-3 text-sm leading-7 text-muted-foreground"><IdentifierText>{t.scenario}</IdentifierText></p>
            <dl className="mt-4 grid gap-3 sm:grid-cols-3">
              {details.scenario.map(([fact, description], i) => <div key={fact}>
                <dt dir="ltr" lang="en" data-testid={`text-scenario-fact-${i}`} className="font-semibold text-primary">{fact}</dt>
                <dd className="mt-1 text-sm leading-7 text-muted-foreground"><IdentifierText>{description}</IdentifierText></dd>
              </div>)}
            </dl>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">{details.scenarioNote}</p>
            <h3 id="about-channels" className="mt-5 font-semibold">{t.channelsTitle}</h3>
            <ul className="mt-2 list-disc space-y-2 ps-5 text-sm text-muted-foreground">
              {t.channels.map((item, i) => <li data-testid={`row-channel-${ABOUT_CHANNELS[i].id}`} key={item}>
                <span data-testid={`about-channel-${i}`}><IdentifierText>{item}</IdentifierText></span>
                <p className="mt-1 leading-7"><IdentifierText>{ABOUT_CHANNELS[i][language][1]}</IdentifierText></p>
              </li>)}
            </ul>
            <h3 className="mt-5 font-semibold">{t.stagesTitle}</h3>
            <ul className="mt-2 list-disc space-y-3 ps-5 text-sm leading-7 text-muted-foreground">
              {t.stages.map((item, i) => <li data-testid={`about-stage-${i}`} key={item}><IdentifierText>{item}</IdentifierText></li>)}
            </ul>
          </section>
          <section id="about-agents" data-testid="about-agents" aria-labelledby="about-agents-title" className={panelClass}>
            <h2 id="about-agents-title" className="text-xl font-semibold">{t.agentsTitle}</h2>
            <dl className="mt-4 space-y-5">
              {t.agents.map(([title, body], i) => (
                <div key={title} data-testid={`about-agent-${i}`}>
                  <dt data-testid={`card-agent-${i + 1}`} className="font-medium text-primary">{title}</dt>
                  <dd className="mt-1 text-sm leading-7 text-muted-foreground"><IdentifierText>{body}</IdentifierText></dd>
                </div>
              ))}
            </dl>
            <p className="mt-4 text-sm leading-7 text-muted-foreground">{details.agentsNote}</p>
          </section>
          {sections.map(section => (
            <section id={`about-${section.id}`} key={section.id} data-testid={`about-${section.id}`} aria-labelledby={`about-${section.id}-title`} className={panelClass}>
              <h2 id={`about-${section.id}-title`} className="text-xl font-semibold">{section.title}</h2>
              <ul className="mt-3 list-disc space-y-3 ps-5 text-sm leading-7 text-muted-foreground">
                {section.items.map((item, i) => <li data-testid={section.id === 'limits' ? `text-limit-${i}` : undefined} key={item}><IdentifierText>{item}</IdentifierText></li>)}
              </ul>
              {section.id === 'assumptions' && <ul className="mt-3 list-disc space-y-3 ps-5 text-sm leading-7 text-muted-foreground">
                {details.assumptions.slice(0, 3).map(item => <li key={item}>{item}</li>)}
              </ul>}
              {section.id === 'ai' && <div data-testid="card-deterministic" className="mt-4 text-sm leading-7 text-muted-foreground"><p className="font-medium">{details.deterministic[0]}</p><p>{details.deterministic[1]}</p></div>}
              {section.id === 'ai' && <div data-testid="card-ai-boundary" className="mt-4 text-sm leading-7 text-muted-foreground"><p className="font-medium"><IdentifierText>{details.ai[0]}</IdentifierText></p><p><IdentifierText>{details.ai[1]}</IdentifierText></p></div>}
              {section.id === 'limits' && <p data-testid="text-limit-3" className="mt-3 text-sm leading-7 text-muted-foreground"><IdentifierText>{details.limits[3]}</IdentifierText></p>}
            </section>
          ))}
          <section data-testid="about-privacy" aria-labelledby="about-privacy-title" className={panelClass}>
            <h2 id="about-privacy-title" className="text-xl font-semibold">{t.privacyTitle}</h2>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">{t.privacy}</p>
          </section>
          <p className="text-xs text-muted-foreground">{details.sources}</p>
        </main>
      </div>
      {notifications && <Panel title={shared.notifications} onClose={() => setNotifications(false)}><p>{shared.noNotifications}</p></Panel>}
    </div>
  );
}
