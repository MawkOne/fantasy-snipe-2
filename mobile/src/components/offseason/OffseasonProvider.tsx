import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from "react";

import type { OffseasonStepId } from "../../data/offseason";

interface OffseasonContextValue {
  /** The stage currently marked as LIVE by the admin. */
  liveStage: OffseasonStepId;
  setLiveStage: (id: OffseasonStepId) => void;
  /** Stages the user has completed (bought out, skipped, etc.). */
  completedStages: OffseasonStepId[];
  completeStage: (id: OffseasonStepId) => void;
}

const OffseasonContext = createContext<OffseasonContextValue | null>(null);

export function OffseasonProvider({ children }: { children: ReactNode }) {
  const [liveStage, setLiveStageState] = useState<OffseasonStepId>("buyouts");
  const [completedStages, setCompletedStages] = useState<OffseasonStepId[]>([]);

  const setLiveStage = useCallback((id: OffseasonStepId) => {
    setLiveStageState(id);
  }, []);

  const completeStage = useCallback((id: OffseasonStepId) => {
    setCompletedStages((prev) =>
      prev.includes(id) ? prev : [...prev, id]
    );
  }, []);

  return (
    <OffseasonContext.Provider
      value={{ liveStage, setLiveStage, completedStages, completeStage }}
    >
      {children}
    </OffseasonContext.Provider>
  );
}

export function useOffseason() {
  const ctx = useContext(OffseasonContext);
  if (!ctx)
    throw new Error("useOffseason must be used within OffseasonProvider");
  return ctx;
}