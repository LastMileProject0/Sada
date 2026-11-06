import { createRoot } from 'react-dom/client';
import { LanguageProvider } from '../../src/lib/i18n';
import { PlanningProvider } from '../../src/lib/planning-state';
import type { ResultsAdapter } from '../../src/lib/results-state';
import { ResultsView } from '../../src/pages/results';
import '../../src/index.css';

// Only this test entry supplies an adapter. The normal app stays disconnected.
// Playwright intercepts the request; it never contacts a real results service.
const adapter: ResultsAdapter = {
  available: true,
  async load(id, signal) {
    const response = await fetch(
      `${import.meta.env.BASE_URL}__e2e/results/${encodeURIComponent(id)}`,
      { signal },
    );
    if (!response.ok) throw new Error('Test results request failed');
    return response.json();
  },
};

createRoot(document.getElementById('root')!).render(
  <LanguageProvider>
    <PlanningProvider>
      <ResultsView resultsAdapter={adapter} />
    </PlanningProvider>
  </LanguageProvider>,
);
