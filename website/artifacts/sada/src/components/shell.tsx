import { useEffect, useRef, useState, type ReactNode } from 'react';
import { useLanguage } from '@/lib/i18n';
import { useLocation, useSearch } from 'wouter';
import { readSavedEvaluationId } from '@/lib/evaluation-session';
import { SiteSearch } from './site-search';
import { Home as HomeIcon, Layers, PlayCircle, Scale, ShieldCheck, Globe, Bell, User, Menu, X, FileText, Info } from 'lucide-react';

const navIcons = [HomeIcon, Layers, PlayCircle, Scale, ShieldCheck, FileText, Info];

export function WaveLogo({ className = '' }: { className?: string }) {
  return (
    <svg viewBox="0 0 120 50" className={className} aria-hidden fill="none" strokeLinecap="round">
      <defs><linearGradient id="wg" x1="0" x2="1"><stop offset="0" stopColor="hsl(182 90% 60%)" /><stop offset=".6" stopColor="hsl(220 85% 65%)" /><stop offset="1" stopColor="hsl(280 80% 68%)" /></linearGradient></defs>
      {[0, 1, 2, 3, 4].map((i) => (
        <path key={i} d={`M4 ${40 - i} C30 ${40 - i} 38 ${30 - i * 2} 50 ${18 - i * 3} S68 ${4 + i * 2} 76 ${14 + i * 2} S96 ${40 - i} 116 ${40 - i}`}
          stroke="url(#wg)" strokeWidth={i === 0 ? 2.4 : 1.2} opacity={1 - i * 0.16}
          style={{ transformOrigin: '60px 40px', animation: `wave ${3 + i * 0.5}s ease-in-out ${i * 0.2}s infinite` }} />
      ))}
    </svg>
  );
}

export function Panel({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  const { t, dir } = useLanguage();
  const dialog = useRef<HTMLDivElement>(null);
  const close = useRef(onClose);
  close.current = onClose;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    dialog.current?.querySelector<HTMLButtonElement>('button')?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') close.current();
      if (event.key === 'Tab') {
        const nodes = dialog.current?.querySelectorAll<HTMLElement>('button, a[href], input, select, textarea, [tabindex="0"]');
        if (!nodes?.length) return;
        const first = nodes[0], last = nodes[nodes.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    };
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('keydown', handleKey);
      previous?.focus();
    };
  }, []);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[hsl(230_60%_3%/.7)] p-4 backdrop-blur-sm" onClick={onClose}>
      <div ref={dialog} dir={dir} role="dialog" aria-modal="true" aria-label={title} className="glass neon-border rise w-full max-w-lg rounded-2xl p-7" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-start justify-between gap-4">
          <h3 className="text-xl font-semibold">{title}</h3>
          <button aria-label={t.close} data-testid="button-close-panel" onClick={onClose} className="rounded-lg p-1.5 text-muted-foreground hover:bg-white/5 hover:text-foreground"><X size={18} /></button>
        </div>
        <div className="space-y-3 text-sm leading-relaxed text-muted-foreground">{children}</div>
      </div>
    </div>
  );
}

export function Sidebar({ active, menu, setMenu, onNav, accessibleAbout = false }: { active: number; menu: boolean; setMenu: (v: boolean) => void; onNav: (i: number) => void; accessibleAbout?: boolean }) {
  const { t, dir } = useLanguage();
  const [, navigate] = useLocation();
  const search = useSearch();
  const sidebar = useRef<HTMLElement>(null);
  const [desktop, setDesktop] = useState(() => window.matchMedia?.('(min-width: 1024px)').matches ?? true);
  useEffect(() => {
    if (!accessibleAbout) return;
    const query = window.matchMedia?.('(min-width: 1024px)');
    if (!query) return;
    const update = () => setDesktop(query.matches);
    update();
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, [accessibleAbout]);
  useEffect(() => {
    if (!accessibleAbout || desktop || !menu) return;
    const previous = document.activeElement as HTMLElement | null;
    const buttons = () => sidebar.current?.querySelectorAll<HTMLButtonElement>('button') ?? [];
    buttons()[0]?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.preventDefault(); setMenu(false); }
      if (event.key !== 'Tab') return;
      const nodes = buttons(), first = nodes[0], last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('keydown', onKey);
      if (previous?.isConnected) previous.focus();
    };
  }, [accessibleAbout, desktop, menu, setMenu]);
  const go = (i: number) => {
    if (i === 6) return navigate('/about');
    if (i !== 4 && i !== 5) return onNav(i);
    // Readiness and reports reuse an explicit evaluation, otherwise the saved session.
    const id = new URLSearchParams(search).get('evaluationId') ?? readSavedEvaluationId();
    const path = i === 4 ? '/readiness' : '/reports';
    navigate(id ? `${path}?evaluationId=${encodeURIComponent(id)}` : path);
  };
  return (
    <>
      <aside ref={sidebar} id={accessibleAbout ? 'about-navigation' : undefined}
        inert={accessibleAbout && !desktop && !menu ? true : undefined}
        aria-hidden={accessibleAbout && !desktop && !menu ? true : undefined}
        role={accessibleAbout && !desktop && menu ? 'dialog' : undefined}
        aria-modal={accessibleAbout && !desktop && menu ? true : undefined}
        aria-label={accessibleAbout ? t.nav[6] : undefined}
        className={`fixed inset-y-0 left-0 z-40 w-60 border-r border-white/5 bg-[hsl(229_50%_7%/.85)] backdrop-blur-xl transition-transform lg:translate-x-0 ${menu ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex flex-col items-center gap-1 px-6 pt-7">
          <WaveLogo className="h-12 w-28 drop-shadow-[0_0_14px_hsl(182_90%_55%/.6)]" />
          <div dir="ltr" className="brand-lockup flex items-center gap-2 text-xl font-bold"><span lang="ar" className="ar">صدى</span><span className="text-white/30">|</span><span lang="en" className="tracking-[0.18em]">SADA</span></div>
        </div>
        <nav aria-label={accessibleAbout ? (dir === 'rtl' ? 'التنقل الرئيسي' : 'Main navigation') : undefined} className="mt-9 space-y-1.5 px-4">
          {navIcons.map((Icon, i) => {
            const on = i === active;
            return (
              <button dir={dir} key={i} data-testid={`nav-${i}`} aria-current={on ? 'page' : undefined} onClick={() => { if (!on || accessibleAbout) setMenu(false); if (!on) go(i); }}
                className={`group flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-start transition ${on ? 'neon-border bg-[hsl(182_80%_45%/.12)] shadow-[0_0_24px_-6px_hsl(182_90%_50%/.6)]' : 'hover:bg-white/[.04]'}`}>
                <Icon size={18} className={on ? 'text-primary' : 'text-muted-foreground group-hover:text-primary'} />
                <span className="text-[13px] font-medium leading-tight">{t.nav[i]}</span>
              </button>
            );
          })}
        </nav>
        <svg aria-hidden={accessibleAbout ? true : undefined} className="absolute bottom-0 left-0 h-48 w-full opacity-70" viewBox="0 0 240 190" preserveAspectRatio="none">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <path key={i} className="dash" style={{ animationDuration: `${8 + i}s` }} d={`M0 ${120 + i * 12} C60 ${90 + i * 10} 120 ${150 + i * 6} 240 ${100 + i * 12}`} fill="none" stroke={i % 2 ? 'hsl(270 70% 62%/.5)' : 'hsl(182 85% 55%/.5)'} strokeWidth=".8" />
          ))}
        </svg>
      </aside>
      {menu && <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={() => setMenu(false)} />}
    </>
  );
}

export function Header({ setMenu, onNotifications, aboutMenuOpen }: { setMenu: (v: boolean) => void; onNotifications: () => void; aboutMenuOpen?: boolean }) {
  const { language, setLanguage, t, dir } = useLanguage();
  return (
    <header className="sticky top-0 z-20 flex items-center gap-4 border-b border-white/5 bg-[hsl(229_50%_7%/.6)] px-5 py-3.5 backdrop-blur-xl md:px-8">
      <button aria-label={t.menu} aria-expanded={aboutMenuOpen} aria-controls={aboutMenuOpen !== undefined ? 'about-navigation' : undefined} aria-haspopup={aboutMenuOpen !== undefined ? 'dialog' : undefined} data-testid="button-menu" className="lg:hidden" onClick={() => setMenu(true)}><Menu size={20} /></button>
      <div className="border-l-2 border-primary pl-3 shadow-[-6px_0_12px_-6px_hsl(182_90%_55%)]">
        <p lang="ar" dir="rtl" className="ar text-[15px] font-medium">تحذير أوضح، وصول أشمل</p>
        <p lang="en" dir="ltr" className="text-xs text-muted-foreground">Clearer Warnings. Wider Reach.</p>
      </div>
      <div className="ml-auto flex items-center gap-3 md:gap-5">
        <SiteSearch />
        <div role="group" aria-label={t.language} className="flex items-center gap-2 text-xs sm:text-sm"><Globe size={16} className="hidden text-muted-foreground sm:block" /><button data-testid="language-ar" aria-pressed={language === 'ar'} onClick={() => setLanguage('ar')} className={language === 'ar' ? 'font-medium text-primary' : 'text-muted-foreground'}>{t.arabic}</button><span className="text-white/20">|</span><button data-testid="language-en" aria-pressed={language === 'en'} onClick={() => setLanguage('en')} className={language === 'en' ? 'font-medium text-primary' : 'text-muted-foreground'}>{t.english}</button></div>
        <button aria-label={t.notifications} data-testid="button-notifications" className="relative" onClick={onNotifications}><Bell size={19} /><span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-secondary shadow-[0_0_8px_hsl(270_80%_65%)]" /></button>
        <span aria-label={t.account} role="img" className="hidden h-9 w-9 place-items-center rounded-full border border-white/15 bg-white/5 sm:grid"><User size={17} /></span>
      </div>
    </header>
  );
}
