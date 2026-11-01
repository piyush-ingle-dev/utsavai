/** Shapes of the data exchanged with the Flask API. Keep in sync with schemas.py on the backend. */

export type EventType = "wedding" | "birthday" | "community";
export type PlanSource = "rules" | "rules+rag" | "ai+rag";
export type ChecklistKey = "timeline" | "vendors";

export interface BudgetLine {
  category: string;
  pct: number;
  amount: number;
}

export interface TimelineItem {
  id: string;
  task: string;
  category: string;
  due: string; // ISO date
  late: boolean;
  done: boolean;
}

export interface VendorItem {
  id: string;
  vendor: string;
  ask: string;
  category: string;
  done: boolean;
}

export interface Idea {
  title: string;
  detail: string;
}

export interface TraceStep {
  agent: string;
  detail: string;
}

export interface PlanData {
  source: PlanSource;
  summary: string;
  budget: BudgetLine[];
  timeline: TimelineItem[];
  vendors: VendorItem[];
  ideas: Idea[];
  vendor_tips: string[];
  risks: string[];
  warnings: string[];
  trace: TraceStep[];
}

export interface PlanResponse {
  id: string;
  title: string;
  event_type: EventType;
  event_label: string;
  event_date: string;
  guests: number;
  budget: number;
  city: string;
  theme: string;
  completed: number;
  total: number;
  can_edit: boolean;
  plan: PlanData;
}

/** What the form holds. Numbers stay as text until the server validates them. */
export interface PlanFormValues {
  event_type: EventType;
  title: string;
  event_date: string;
  guests: string;
  budget: string;
  city: string;
  theme: string;
  preferences: string;
}

export interface CreatedPlan {
  id: string;
  edit_token: string;
}

export interface ToggleResult {
  id: string;
  done: boolean;
  completed: number;
  total: number;
}

export interface AskReply {
  answer: string;
  sources: string[];
}
