// Thin wrapper over the Flask REST API. Every call returns parsed JSON or throws an Error
// that carries .status and, for validation problems, .errors (a map of field -> message).
//
// Each plan has an "edit token" that the server hands out once, when the plan is created.
// We keep it in this browser's localStorage and send it with every request about that plan.
// Anyone who only has the link can read the plan but cannot change it.

const tokenKey = (planId) => `utsavai:edit:${planId}`;

export function saveEditToken(planId, token) {
  try {
    localStorage.setItem(tokenKey(planId), token);
  } catch {
    // Storage can be blocked (private mode). The plan is then view-only after a reload.
  }
}

function loadEditToken(planId) {
  try {
    return localStorage.getItem(tokenKey(planId)) || "";
  } catch {
    return "";
  }
}

async function request(path, { planId, ...options } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = planId ? loadEditToken(planId) : "";
  if (token) headers["X-Edit-Token"] = token;

  const res = await fetch(path, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.error || "Something went wrong. Please try again.");
    err.status = res.status;
    err.errors = data.errors || {};
    throw err;
  }
  return data;
}

const post = (path, body, planId) => request(path, { method: "POST", body: JSON.stringify(body), planId });

export const createPlan = (body) => post("/api/plans", body);
export const getPlan = (id) => request(`/api/plans/${id}`, { planId: id });
export const toggleItem = (id, itemId) => post(`/api/plans/${id}/toggle`, { id: itemId }, id);
export const askPlanner = (id, question) => post(`/api/plans/${id}/ask`, { question }, id);
