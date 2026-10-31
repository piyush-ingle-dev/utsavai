import { useState } from "react";
import { askPlanner } from "../api.js";

export default function AskPlanner({ planId }) {
  const [question, setQuestion] = useState("");
  const [reply, setReply] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      setReply(await askPlanner(planId, question));
    } catch (err) {
      setReply(null);
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card noprint" aria-labelledby="h-ask">
      <h2 id="h-ask">Ask the planner</h2>
      <form onSubmit={submit} className="ask">
        <label htmlFor="question" className="sr">Your question</label>
        <input id="question" value={question} maxLength={300} onChange={(e) => setQuestion(e.target.value)}
               placeholder="How do I handle loudspeaker permissions?" />
        <button className="btn" type="submit" disabled={busy || question.trim().length < 3}>
          {busy ? "Thinking..." : "Ask"}
        </button>
      </form>
      <div role="status" aria-live="polite">
        {error && <p className="err">{error}</p>}
        {reply && (
          <div className="answer">
            <p>{reply.answer}</p>
            {reply.sources.length > 0 && <p className="muted">Sources: {reply.sources.join(", ")}</p>}
          </div>
        )}
      </div>
    </section>
  );
}
