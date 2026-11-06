import { createContext, useContext, type ReactNode } from 'react';
import { useSimulation } from './simulation';
import { sadaSimulationAdapter } from './sada-api-adapters';

const SimulationContext = createContext<ReturnType<typeof useSimulation> | null>(null);

/** Execution survives route changes; refresh revalidates the saved ID with Python. */
export function SimulationProvider({ children }: { children: ReactNode }) {
  const simulation = useSimulation(sadaSimulationAdapter);
  return <SimulationContext.Provider value={simulation}>{children}</SimulationContext.Provider>;
}

export function useLiveSimulation() {
  const simulation = useContext(SimulationContext);
  if (!simulation) throw new Error('SimulationProvider is required');
  return simulation;
}
