import type { AskReply, CreatedPlan, PlanFormValues, PlanResponse, ToggleResult } from "./types";

// Thin wrapper over the Flask REST API.
//
// Each plan has an "edit token" that the server hands out once, when the plan is created.
// We keep it in this browser's localStorage and send it with every request about that plan.
// Anyone who only has the link can read the plan but cannot change it.

const EDIT_HEADER = "X-Edit-Token";
const FALLBACK_MESSAGE = "Something went wrong. Please try again.";

/** An error answer from the API. `fieldErrors` maps form field names to messages for validation failures. */
export class ApiError extends Error {
  readonly status: number;
  readonly fieldErrors: Record<string, string>;

  constructor(message: string, status: number, fieldErrors: Record<string, string> = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

const tokenKey = (planId: string): string => `utsavai:edit:${planId}`;

export function saveEditToken(planId: string, token: string): void {
  try {
    localStorage.setItem(tokenKey(planId), token);
  } catch {
    // Storage can be blocked (private mode). The plan is then view-only after a reload.
  }
}

function loadEditToken(planId: string): string {
  try {
    return localStorage.getItem(tokenKey(planId)) ?? "";
  } catch {
    return "";
  }
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  planId?: string;
}

async function request<T>(path: string, { method = "GET", body, planId }: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = planId ? loadEditToken(planId) : "";
  if (token) headers[EDIT_HEADER] = token;

  const response = await fetch(path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const problem = (data ?? {}) as { error?: string; errors?: Record<string, string> };
    throw new ApiError(problem.error ?? FALLBACK_MESSAGE, response.status, problem.errors ?? {});
  }
  return data as T;
}

export const createPlan = (values: PlanFormValues): Promise<CreatedPlan> =>
  request("/api/plans", { method: "POST", body: values });

export const getPlan = (planId: string): Promise<PlanResponse> => request(`/api/plans/${planId}`, { planId });

export const toggleItem = (planId: string, itemId: string): Promise<ToggleResult> =>
  request(`/api/plans/${planId}/toggle`, { method: "POST", body: { id: itemId }, planId });

export const askPlanner = (planId: string, question: string): Promise<AskReply> =>
  request(`/api/plans/${planId}/ask`, { method: "POST", body: { question }, planId });
