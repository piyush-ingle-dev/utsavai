import { useEffect, useState } from "react";
import { getPlan, toggleItem } from "../api.js";
import AgentTrace from "./AgentTrace.jsx";
import AskPlanner from "./AskPlanner.jsx";

const rupees = (n) => n.toLocaleString("en-IN");
const dmy = (iso) => `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}`;

export default function PlanView({ planId, onNew }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [saveError, setSaveError] = useState("");

  useEffect(() => {
    let alive = true;
    setData(null);
    setError("");
    getPlan(planId)
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(e.status === 404 ? "We could not find that plan." : e.message));
    return () => { alive = false; };
  }, [planId]);

  if (error) {
    return (
      <section className="hero">
        <h1>Plan not found</h1>
        <p>{error}</p>
        <button className="btn" onClick={onNew}>Back to the planner</button>
      </section>
    );
  }
  if (!data) return <p role="status">Loading your plan...</p>;

  const { plan } = data;

  async function toggle(listName, itemId) {
    setSaveError("");
    const flip = (d) => ({
      ...d,
      plan: { ...d.plan, [listName]: d.plan[listName].map((i) => (i.id === itemId ? { ...i, done: !i.done } : i)) },
    });
    setData(flip); // show the change straight away
    try {
      const res = await toggleItem(planId, itemId);
      setData((d) => ({ ...d, completed: res.completed, total: res.total }));
    } catch {
      setData(flip); // undo
      setSaveError("Could not save that change. Please try again.");
    }
  }

  return (
    <>
      <section className="hero">
        <h1>{data.title}</h1>
        <p>{plan.summary}</p>
        <p className="meta">
          <span>{data.event_label}</span>
          <span>{dmy(data.event_date)}</span>
          <span>{data.guests} guests</span>
          {data.city && <span>{data.city}</span>}
          {data.theme && <span>{data.theme}</span>}
        </p>
        <p className="actions noprint">
          <a className="btn secondary" href={`/api/plans/${planId}/calendar.ics`}>Add timeline to calendar</a>
          <button className="btn secondary" onClick={() => window.print()}>Print or save as PDF</button>
          <button className="btn secondary" onClick={onNew}>New plan</button>
        </p>
        <p role="status" aria-live="polite">
          {data.completed} of {data.total} items done{" "}
          <progress value={data.completed} max={data.total} />
        </p>
        {saveError && <div className="alert" role="alert">{saveError}</div>}
      </section>

      {plan.warnings.map((w) => <div className="alert" role="note" key={w}>{w}</div>)}

      <section className="card" aria-labelledby="h-budget">
        <h2 id="h-budget">Budget split</h2>
        <table>
          <caption className="sr">Budget by category</caption>
          <thead><tr><th scope="col">Category</th><th scope="col">Share</th><th scope="col" className="num">Amount (Rs)</th></tr></thead>
          <tbody>
            {plan.budget.map((r) => (
              <tr key={r.category}>
                <th scope="row">{r.category}</th>
                <td><meter min="0" max="40" value={r.pct} aria-label={`${r.category} ${r.pct} percent`} /> {r.pct}%</td>
                <td className="num">{rupees(r.amount)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot><tr><th scope="row" colSpan="2">Total</th><td className="num">{rupees(data.budget)}</td></tr></tfoot>
        </table>
      </section>

      <section className="card" aria-labelledby="h-timeline">
        <h2 id="h-timeline">Timeline</h2>
        <ul className="checklist">
          {plan.timeline.map((t) => (
            <li key={t.id}>
              <label>
                <input type="checkbox" checked={t.done} onChange={() => toggle("timeline", t.id)} />
                <span>
                  <strong>{dmy(t.due)}</strong> {t.task} <em className="chip">{t.category}</em>
                  {t.late && <em className="chip warn">compressed</em>}
                </span>
              </label>
            </li>
          ))}
        </ul>
      </section>

      <section className="card" aria-labelledby="h-vendors">
        <h2 id="h-vendors">Vendor checklist</h2>
        <ul className="checklist">
          {plan.vendors.map((v) => (
            <li key={v.id}>
              <label>
                <input type="checkbox" checked={v.done} onChange={() => toggle("vendors", v.id)} />
                <span><strong>{v.vendor}</strong><br /><span className="muted">Ask about: {v.ask}</span></span>
              </label>
            </li>
          ))}
        </ul>
        {plan.vendor_tips.length > 0 && (
          <>
            <h3>Tips</h3>
            <ul>{plan.vendor_tips.map((t) => <li key={t}>{t}</li>)}</ul>
          </>
        )}
      </section>

      <section className="card" aria-labelledby="h-ideas">
        <h2 id="h-ideas">Ideas for your event</h2>
        <ul className="ideas">
          {plan.ideas.map((i) => <li key={i.title}><strong>{i.title}</strong><br />{i.detail}</li>)}
        </ul>
      </section>

      {plan.risks.length > 0 && (
        <section className="card" aria-labelledby="h-risks">
          <h2 id="h-risks">What could go wrong</h2>
          <ul>{plan.risks.map((r) => <li key={r}>{r}</li>)}</ul>
        </section>
      )}

      <AskPlanner planId={planId} />
      <AgentTrace trace={plan.trace} source={plan.source} />
    </>
  );
}
