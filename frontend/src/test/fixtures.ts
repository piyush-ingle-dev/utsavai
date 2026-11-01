import type { PlanResponse } from "../types";

export const PLAN_ID = "a".repeat(32);

export function makePlan(overrides: Partial<PlanResponse> = {}): PlanResponse {
  return {
    id: PLAN_ID,
    title: "Riya and Aman",
    event_type: "wedding",
    event_label: "Wedding",
    event_date: "2026-12-30",
    guests: 150,
    budget: 500000,
    city: "Nagpur",
    theme: "Royal",
    completed: 0,
    total: 3,
    can_edit: true,
    plan: {
      source: "rules+rag",
      summary: "A wedding for 150 guests.",
      budget: [
        { category: "Venue", pct: 60, amount: 300000 },
        { category: "Contingency", pct: 40, amount: 200000 },
      ],
      timeline: [
        { id: "t0", task: "Book the venue", category: "Venue", due: "2026-10-01", late: false, done: false },
        { id: "t1", task: "Send invitations", category: "Invitations", due: "2026-11-01", late: true, done: false },
      ],
      vendors: [{ id: "v0", vendor: "Caterer", ask: "Tasting and rates", category: "Catering", done: false }],
      ideas: [{ title: "Memory wall", detail: "Printed photos at the entrance." }],
      vendor_tips: ["Get quotes in writing"],
      risks: ["Rain: keep a covered area"],
      warnings: ["Your budget is tight"],
      trace: [
        { agent: "Researcher", detail: "Retrieved 5 guide passages" },
        { agent: "Critic", detail: "All checks passed" },
      ],
    },
    ...overrides,
  };
}
