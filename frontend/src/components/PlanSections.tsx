import type { Idea } from "../types";

export function IdeasSection({ ideas }: { ideas: Idea[] }) {
  return (
    <section className="card" aria-labelledby="h-ideas">
      <h2 id="h-ideas">Ideas for your event</h2>
      <ul className="ideas">
        {ideas.map(({ title, detail }) => (
          <li key={title}>
            <strong>{title}</strong>
            <br />
            {detail}
          </li>
        ))}
      </ul>
    </section>
  );
}

export function RisksSection({ risks }: { risks: string[] }) {
  if (risks.length === 0) return null;
  return (
    <section className="card" aria-labelledby="h-risks">
      <h2 id="h-risks">What could go wrong</h2>
      <ul>
        {risks.map((risk) => (
          <li key={risk}>{risk}</li>
        ))}
      </ul>
    </section>
  );
}
