const LABELS = {
  "ai+rag": "Written by the LLM using the retrieved planning guide",
  "rules+rag": "Built from rules and the retrieved planning guide",
};

export default function AgentTrace({ trace = [], source }) {
  return (
    <section className="card noprint" aria-labelledby="h-trace">
      <h2 id="h-trace">How this plan was made</h2>
      <p className="muted">{LABELS[source] || "Built from rules"}. Each step below is one agent in the pipeline.</p>
      <ol className="trace">
        {trace.map((s, i) => (
          <li key={i}><strong>{s.agent}</strong> {s.detail}</li>
        ))}
      </ol>
    </section>
  );
}
