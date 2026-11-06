import { createContext, useContext, useRef, useState, type ReactNode } from 'react';
import { clearSavedEvaluation } from './evaluation-session';

export const STAGES = ['T+00', 'T+02', 'T+04', 'T+06'] as const;
export const CHANNEL_IDS = ['CH01', 'CH02', 'CH03', 'CH04', 'CH05'] as const;
export type Stage = typeof STAGES[number];
export type ChannelId = typeof CHANNEL_IDS[number];

interface PlanningSelection {
  stage: Stage;
  enabledChannels: ChannelId[];
}

export const planningStorageKey = 'sada-planning-selection';
export const evaluationHandoffKey = 'sada-evaluation-handoff';

function initialSelection(): PlanningSelection {
  try {
    const saved: unknown = JSON.parse(localStorage.getItem(planningStorageKey) ?? 'null');
    if (saved && typeof saved === 'object' && 'stage' in saved && 'enabledChannels' in saved &&
      STAGES.includes(saved.stage as Stage) && Array.isArray(saved.enabledChannels)) {
      const channels = CHANNEL_IDS.filter((id) => (saved.enabledChannels as unknown[]).includes(id));
      if (channels.length > 0) return { stage: saved.stage as Stage, enabledChannels: channels };
    }
  } catch { /* Invalid or unavailable storage must not prevent planning. */ }
  return { stage: 'T+00', enabledChannels: [...CHANNEL_IDS] };
}

function requestedEvaluation() {
  try {
    const handoff = JSON.parse(localStorage.getItem(evaluationHandoffKey) ?? 'null');
    const selection = initialSelection();
    return handoff?.status === 'requested' && handoff.scenario === 'AL_WADI_FLASH_FLOOD' &&
      handoff.stage === selection.stage &&
      JSON.stringify(handoff.enabledChannelIds) === JSON.stringify(selection.enabledChannels);
  } catch { return false; }
}

interface PlanningContextValue extends PlanningSelection {
  setStage: (stage: Stage) => void;
  toggleChannel: (id: ChannelId) => boolean;
  runEvaluation: () => void;
  evaluationPending: boolean;
  clearPending: () => void;
}

const PlanningContext = createContext<PlanningContextValue | null>(null);

export function PlanningProvider({ children }: { children: ReactNode }) {
  const [selection, setSelection] = useState<PlanningSelection>(initialSelection);
  const current = useRef(selection);
  const [evaluationPending, setEvaluationPending] = useState(requestedEvaluation);

  function update(next: PlanningSelection) {
    current.current = next;
    setSelection(next);
    setEvaluationPending(false);
    clearSavedEvaluation();
    try {
      localStorage.setItem(planningStorageKey, JSON.stringify(next));
      localStorage.removeItem(evaluationHandoffKey);
    } catch { /* In-memory state remains usable if storage is blocked. */ }
  }

  function setStage(stage: Stage) {
    if (STAGES.includes(stage)) update({ ...current.current, stage });
  }

  function toggleChannel(id: ChannelId): boolean {
    if (!CHANNEL_IDS.includes(id)) return false;
    const previous = current.current;
    const enabled = previous.enabledChannels.includes(id);
    if (enabled && previous.enabledChannels.length === 1) return false;
    const next = enabled
      ? previous.enabledChannels.filter((channel) => channel !== id)
      : CHANNEL_IDS.filter((channel) => channel === id || previous.enabledChannels.includes(channel));
    update({ ...previous, enabledChannels: next });
    return true;
  }

  function runEvaluation() {
    // Simulation consumes this handoff and sends the exact selected configuration.
    clearSavedEvaluation();
    try {
      localStorage.setItem(evaluationHandoffKey, JSON.stringify({
        scenario: 'AL_WADI_FLASH_FLOOD',
        stage: current.current.stage,
        enabledChannelIds: current.current.enabledChannels,
        status: 'requested',
      }));
    } catch { /* Selection is also retained by the provider while navigating. */ }
    setEvaluationPending(true);
  }

  return <PlanningContext.Provider value={{
    ...selection, setStage, toggleChannel, runEvaluation,
    evaluationPending, clearPending: () => {
      setEvaluationPending(false);
      try { localStorage.removeItem(evaluationHandoffKey); } catch { /* Storage is optional. */ }
    },
  }}>{children}</PlanningContext.Provider>;
}

export function usePlanning() {
  const value = useContext(PlanningContext);
  if (!value) throw new Error('PlanningProvider is required');
  return value;
}
