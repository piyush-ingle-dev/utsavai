import { dayMonthYear } from "../lib/format";
import type { PlanResponse } from "../types";

interface PlanHeaderProps {
  plan: PlanResponse;
  saveError: string;
  onNew: () => void;
}

export default function PlanHeader({ plan, saveError, onNew }: PlanHeaderProps) {
  return (
    <section className="hero">
      <h1>{plan.title}</h1>
      <p>{plan.plan.summary}</p>
      <p className="meta">
        <span>{plan.event_label}</span>
        <span>{dayMonthYear(plan.event_date)}</span>
        <span>{plan.guests} guests</span>
        {plan.city && <span>{plan.city}</span>}
        {plan.theme && <span>{plan.theme}</span>}
      </p>
      <p className="actions noprint">
        <a className="btn secondary" href={`/api/plans/${plan.id}/calendar.ics`}>
          Add timeline to calendar
        </a>
        <button type="button" className="btn secondary" onClick={() => window.print()}>
          Print or save as PDF
        </button>
        <button type="button" className="btn secondary" onClick={onNew}>
          New plan
        </button>
      </p>
      <p role="status" aria-live="polite">
        {plan.completed} of {plan.total} items done{" "}
        <progress value={plan.completed} max={plan.total} aria-label="Checklist progress" />
      </p>
      {saveError && (
        <div className="alert" role="alert">
          {saveError}
        </div>
      )}
      {!plan.can_edit && (
        <p className="muted" role="note">
          View only. Checklists can be ticked from the browser where this plan was created.
        </p>
      )}
    </section>
  );
}
