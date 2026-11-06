import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react';
import { Search, X } from 'lucide-react';
import { useLocation, useSearch } from 'wouter';
import { useLanguage } from '@/lib/i18n';
import { readSavedEvaluationId } from '@/lib/evaluation-session';
import { searchCopy, searchDestination, searchPages } from '@/lib/site-search';

export function SiteSearch() {
  const { language, dir, t } = useLanguage();
  const c = searchCopy[language];
  const [location, navigate] = useLocation();
  const search = useSearch();
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const host = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const mobileInput = useRef<HTMLInputElement>(null);
  const mobileTrigger = useRef<HTMLButtonElement>(null);
  const listId = useId();
  const matches = searchPages(query, language);
  useEffect(() => {
    setOpen(false); setQuery(''); setActive(0);
  }, [location]);
  useEffect(() => {
    const outside = (event: PointerEvent) => {
      if (!host.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('pointerdown', outside);
    return () => document.removeEventListener('pointerdown', outside);
  }, []);
  const choose = (path: string) => {
    const id = new URLSearchParams(search).get('evaluationId') ?? readSavedEvaluationId();
    setOpen(false); setQuery(''); setActive(0);
    navigate(searchDestination(path, id));
  };
  const key = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Escape') {
      if (event.currentTarget === mobileInput.current) mobileTrigger.current?.focus();
      setOpen(false); event.preventDefault();
    }
    else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault(); setOpen(true);
      setActive(i => matches.length ? (i + (event.key === 'ArrowDown' ? 1 : -1) + matches.length) % matches.length : 0);
    } else if (event.key === 'Enter') {
      event.preventDefault();
      if (matches[active]) choose(matches[active].path);
    }
  };
  const field = (mobile: boolean) => (
    <input ref={mobile ? mobileInput : input} dir={dir} role="combobox" aria-autocomplete="list"
      aria-label={c.label} aria-expanded={open} aria-controls={listId}
      aria-activedescendant={open && matches[active] ? `${listId}-${active}` : undefined}
      data-testid={mobile ? 'input-search-mobile' : 'input-search'} autoComplete="off" maxLength={128}
      placeholder={t.search} value={query} onFocus={() => setOpen(true)} onClick={() => setOpen(true)} onKeyDown={key}
      onChange={e => { setQuery(e.target.value); setActive(0); setOpen(true); }}
      className={mobile ? 'min-w-0 flex-1 bg-transparent py-2 text-sm outline-none' : 'w-36 bg-transparent outline-none placeholder:text-muted-foreground'} />
  );
  return (
    <div ref={host} className="min-w-0 md:relative" dir={dir} onBlur={event => {
      if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setOpen(false);
    }}>
      <label className="glass hidden items-center gap-2 rounded-full px-4 py-2 text-sm md:flex">
        <Search size={15} className="shrink-0 text-muted-foreground" />{field(false)}
      </label>
      <button ref={mobileTrigger} type="button" data-testid="button-mobile-search" aria-label={c.open} aria-expanded={open}
        onClick={() => { setOpen(v => !v); requestAnimationFrame(() => mobileInput.current?.focus()); }}
        className="grid h-8 w-8 place-items-center rounded-full border border-white/10 md:hidden"><Search size={16} /></button>
      {open && (
        <div data-testid="search-panel" className="glass absolute inset-x-4 top-full z-50 mt-3 max-h-[65dvh] overflow-y-auto rounded-2xl border border-primary/30 bg-[hsl(229_50%_8%)] p-3 shadow-2xl md:inset-x-auto md:end-0 md:w-[22rem]">
          <div className="flex items-center gap-2 border-b border-white/10 md:hidden">
            {field(true)}
            <button type="button" aria-label={c.clear} onClick={() => { setQuery(''); setActive(0); mobileInput.current?.focus(); }}><X size={14} /></button>
          </div>
          <p className="mb-2 text-[11px] leading-relaxed text-muted-foreground">{c.scope}</p>
          <div id={listId} role="listbox" aria-label={c.label}>
            {matches.map((page, i) => (
              <button key={page.path} id={`${listId}-${i}`} type="button" role="option" aria-selected={i === active} tabIndex={-1}
                data-testid={`search-result-${page.path === '/' ? 'home' : page.path.slice(1)}`}
                onClick={() => choose(page.path)} onMouseEnter={() => setActive(i)}
                className={`block w-full rounded-lg px-3 py-2 text-start text-sm ${i === active ? 'bg-primary/15 text-primary' : 'hover:bg-white/5'}`}>{page.title}</button>
            ))}
          </div>
          {!matches.length && <div role="status" data-testid="search-no-results" className="px-2 py-4 text-sm"><p>{c.none}</p><p className="mt-1 text-xs text-muted-foreground">{c.hint}</p></div>}
        </div>
      )}
    </div>
  );
}
