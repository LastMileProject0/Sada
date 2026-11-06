import { createRoot } from 'react-dom/client';

import App from './App';
import { ErrorBoundary } from '@/components/error-boundary';

import './index.css';
import { LanguageProvider } from '@/lib/i18n';
import { PlanningProvider } from '@/lib/planning-state';
import { SimulationProvider } from '@/lib/simulation-state';

createRoot(document.getElementById('root')!, {
  // Keeps caught errors off reportError(), which would raise the dev overlay.
  onCaughtError: (error, errorInfo) => {
    console.error(error, errorInfo.componentStack);
  },
}).render(
  <LanguageProvider>
    <ErrorBoundary>
      <PlanningProvider>
        <SimulationProvider><App /></SimulationProvider>
      </PlanningProvider>
    </ErrorBoundary>
  </LanguageProvider>,
);
