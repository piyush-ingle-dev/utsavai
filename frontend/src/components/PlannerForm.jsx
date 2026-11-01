import { useEffect, useRef, useState } from "react";
import { createPlan, saveEditToken } from "../api.js";

const TYPES = [
  { key: "wedding", label: "Wedding" },
  { key: "birthday", label: "Birthday" },
  { key: "community", label: "Community event" },
];

function isoDate(daysAhead) {
  const d = new Date();
  d.setDate(d.getDate() + daysAhead);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export default function PlannerForm({ onCreated }) {
  const [values, setValues] = useState({
    event_type: "wedding", title: "", event_date: isoDate(60), guests: "", budget: "",
    city: "", theme: "", preferences: "",
  });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const alertRef = useRef(null);

  useEffect(() => {
    if ((message || Object.keys(errors).length) && alertRef.current) alertRef.current.focus();
  }, [message, errors]);

  const set = (name) => (e) => setValues((v) => ({ ...v, [name]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    setMessage("");
    try {
      const { id, edit_token: editToken } = await createPlan(values);
      saveEditToken(id, editToken);
      onCreated(id);
    } catch (err) {
      setErrors(err.errors || {});
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  }

  const field = (name, label, props = {}) => (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      <input id={name} name={name} value={values[name]} onChange={set(name)}
             aria-invalid={errors[name] ? "true" : undefined}
             aria-describedby={errors[name] ? `${name}-err` : undefined} {...props} />
      {errors[name] && <span className="err" id={`${name}-err`}>{errors[name]}</span>}
    </div>
  );

  return (
    <>
      <section className="hero">
        <h1>Plan your celebration in one minute</h1>
        <p>Tell us a few details. A team of AI agents researches, plans and double-checks a budget split, a dated timeline, a vendor checklist and ideas for your event.</p>
      </section>

      <form className="card" onSubmit={submit} noValidate aria-busy={busy}>
        {message && <div className="alert" role="alert" tabIndex={-1} ref={alertRef}>{message}</div>}

        <fieldset>
          <legend>Event type</legend>
          <div className="choices">
            {TYPES.map((t) => (
              <label className="choice" key={t.key}>
                <input type="radio" name="event_type" value={t.key}
                       checked={values.event_type === t.key} onChange={set("event_type")} />
                <span>{t.label}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="grid">
          {field("title", "Event name (optional)", { maxLength: 120, placeholder: "Riya and Aman's wedding" })}
          {field("event_date", "Event date", { type: "date", min: isoDate(0), required: true })}
          {field("guests", "Number of guests", { inputMode: "numeric", placeholder: "150", required: true })}
          {field("budget", "Total budget (Rs)", { inputMode: "numeric", placeholder: "500000", required: true })}
          {field("city", "City (optional)", { maxLength: 80, placeholder: "Nagpur" })}
          {field("theme", "Theme (optional)", { maxLength: 80, placeholder: "Royal Maharashtrian" })}
        </div>

        <div className="field">
          <label htmlFor="preferences">Anything special? (optional)</label>
          <textarea id="preferences" rows="3" maxLength={500} value={values.preferences} onChange={set("preferences")}
                    placeholder="Pure veg menu, outdoor evening, elderly guests need seating" />
        </div>

        <button className="btn" type="submit" disabled={busy}>
          {busy ? "Agents are planning..." : "Create my plan"}
        </button>
        {busy && <p className="muted" role="status">Researching, planning and checking your event. This can take up to 20 seconds.</p>}
      </form>
    </>
  );
}
