import { useCallback, useEffect, useState } from "react";
import { ApiError, getPlan, toggleItem } from "../api";
import type { ChecklistKey, PlanResponse } from "../types";

interface UsePlan {
  plan: PlanResponse | null;
  /** Set when the plan could not be loaded. */
  error: string;
  /** Set when a checklist change could not be saved. */
  saveError: string;
  toggle: (list: ChecklistKey, itemId: string) => Promise<void>;
}

const flipItem = (current: PlanResponse, list: ChecklistKey, itemId: string): PlanResponse => ({
  ...current,
  plan: {
    ...current.plan,
    [list]: current.plan[list].map((item) => (item.id === itemId ? { ...item, done: !item.done } : item)),
  },
});

/** Loads one plan and offers an optimistic checklist toggle (shows the change at once, undoes it on failure). */
export function usePlan(planId: string): UsePlan {
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [error, setError] = useState("");
  const [saveError, setSaveError] = useState("");

  useEffect(() => {
    let active = true;
    setPlan(null);
    setError("");
    getPlan(planId)
      .then((loaded) => active && setPlan(loaded))
      .catch((failure: unknown) => {
        if (!active) return;
        const notFound = failure instanceof ApiError && failure.status === 404;
        setError(notFound ? "We could not find that plan." : failure instanceof Error ? failure.message : "Error");
      });
    return () => {
      active = false;
    };
  }, [planId]);

  const toggle = useCallback(
    async (list: ChecklistKey, itemId: string): Promise<void> => {
      setSaveError("");
      setPlan((current) => current && flipItem(current, list, itemId));
      try {
        const result = await toggleItem(planId, itemId);
        setPlan((current) => current && { ...current, completed: result.completed, total: result.total });
      } catch {
        setPlan((current) => current && flipItem(current, list, itemId));
        setSaveError("Could not save that change. Please try again.");
      }
    },
    [planId],
  );

  return { plan, error, saveError, toggle };
}
