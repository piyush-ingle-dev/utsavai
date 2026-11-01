import type { PlanSource, TraceStep } from "../types";

const SOURCE_LABELS: Record<PlanSource, string> = {
  "ai+rag": "Written by the LLM using the retrieved planning guide",
  "rules+rag": "Built from rules and the retrieved planning guide",
  rules: "Built from rules",
};

interface AgentTraceProps {
  trace: TraceStep[];
  source: PlanSource;
}

export default function AgentTrace({ trace, source }: AgentTraceProps) {
  return (
    <section className="card noprint" aria-labelledby="h-trace">
      <h2 id="h-trace">How this plan was made</h2>
      <p className="muted">{SOURCE_LABELS[source]}. Each step below is one agent in the pipeline.</p>
      <ol className="trace">
        {trace.map((step, index) => (
          <li key={`${step.agent}-${index}`}>
            <strong>{step.agent}</strong> {step.detail}
          </li>
        ))}
      </ol>
    </section>
  );
}
