import { useState } from "react";
import type { FormEvent } from "react";
import { askPlanner } from "../api";
import type { AskReply } from "../types";

const MIN_QUESTION_LENGTH = 3;

export default function AskPlanner({ planId }: { planId: string }) {
  const [question, setQuestion] = useState("");
  const [reply, setReply] = useState<AskReply | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      setReply(await askPlanner(planId, question));
    } catch (failure) {
      setReply(null);
      setError(failure instanceof Error ? failure.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card noprint" aria-labelledby="h-ask">
      <h2 id="h-ask">Ask the planner</h2>
      <form onSubmit={submit} className="ask">
        <label htmlFor="question" className="sr">
          Your question
        </label>
        <input
          id="question"
          value={question}
          maxLength={300}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="How do I handle loudspeaker permissions?"
        />
        <button className="btn" type="submit" disabled={busy || question.trim().length < MIN_QUESTION_LENGTH}>
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
