import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { ApiError, createPlan, saveEditToken } from "../api";
import { isoDate } from "../lib/format";
import type { EventType, PlanFormValues } from "../types";
import TextField from "./TextField";

const EVENT_TYPES: { key: EventType; label: string }[] = [
  { key: "wedding", label: "Wedding" },
  { key: "birthday", label: "Birthday" },
  { key: "community", label: "Community event" },
];
const DEFAULT_LEAD_DAYS = 60;

interface PlannerFormProps {
  onCreated: (planId: string) => void;
}

export default function PlannerForm({ onCreated }: PlannerFormProps) {
  const [values, setValues] = useState<PlanFormValues>({
    event_type: "wedding",
    title: "",
    event_date: isoDate(DEFAULT_LEAD_DAYS),
    guests: "",
    budget: "",
    city: "",
    theme: "",
    preferences: "",
  });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const alertRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (message) alertRef.current?.focus();
  }, [message]);

  const update = (name: string, value: string): void => setValues((current) => ({ ...current, [name]: value }));

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setBusy(true);
    setFieldErrors({});
    setMessage("");
    try {
      const { id, edit_token: editToken } = await createPlan(values);
      saveEditToken(id, editToken);
      onCreated(id);
    } catch (failure) {
      setFieldErrors(failure instanceof ApiError ? failure.fieldErrors : {});
      setMessage(failure instanceof Error ? failure.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  const text = (name: keyof PlanFormValues, label: string, extra: Record<string, unknown> = {}) => (
    <TextField name={name} label={label} value={values[name]} error={fieldErrors[name]} onChange={update} {...extra} />
  );

  return (
    <>
      <section className="hero">
        <h1>Plan your celebration in one minute</h1>
        <p>
          Tell us a few details. A team of AI agents researches, plans and double-checks a budget split, a dated
          timeline, a vendor checklist and ideas for your event.
        </p>
      </section>

      <form className="card" onSubmit={submit} noValidate aria-busy={busy}>
        {message && (
          <div className="alert" role="alert" tabIndex={-1} ref={alertRef}>
            {message}
          </div>
        )}

        <fieldset>
          <legend>Event type</legend>
          <div className="choices">
            {EVENT_TYPES.map(({ key, label }) => (
              <label className="choice" key={key}>
                <input
                  type="radio"
                  name="event_type"
                  value={key}
                  checked={values.event_type === key}
                  onChange={() => update("event_type", key)}
                />
                <span>{label}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="grid">
          {text("title", "Event name (optional)", { maxLength: 120, placeholder: "Riya and Aman's wedding" })}
          {text("event_date", "Event date", { type: "date", min: isoDate(0), required: true })}
          {text("guests", "Number of guests", { inputMode: "numeric", placeholder: "150", required: true })}
          {text("budget", "Total budget (Rs)", { inputMode: "numeric", placeholder: "500000", required: true })}
          {text("city", "City (optional)", { maxLength: 80, placeholder: "Nagpur" })}
          {text("theme", "Theme (optional)", { maxLength: 80, placeholder: "Royal Maharashtrian" })}
        </div>

        <div className="field">
          <label htmlFor="preferences">Anything special? (optional)</label>
          <textarea
            id="preferences"
            rows={3}
            maxLength={500}
            value={values.preferences}
            onChange={(event) => update("preferences", event.target.value)}
            placeholder="Pure veg menu, outdoor evening, elderly guests need seating"
          />
        </div>

        <button className="btn" type="submit" disabled={busy}>
          {busy ? "Agents are planning..." : "Create my plan"}
        </button>
        {busy && (
          <p className="muted" role="status">
            Researching, planning and checking your event. This can take up to 20 seconds.
          </p>
        )}
      </form>
    </>
  );
}
