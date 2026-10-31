// Thin wrapper over the Flask REST API. Every call returns parsed JSON or throws an Error
// that carries .status and, for validation problems, .errors (a map of field -> message).
async function request(path, options = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.error || "Something went wrong. Please try again.");
    err.status = res.status;
    err.errors = data.errors || {};
    throw err;
  }
  return data;
}

const post = (path, body) => request(path, { method: "POST", body: JSON.stringify(body) });

export const createPlan = (body) => post("/api/plans", body);
export const getPlan = (id) => request(`/api/plans/${id}`);
export const toggleItem = (id, itemId) => post(`/api/plans/${id}/toggle`, { id: itemId });
export const askPlanner = (id, question) => post(`/api/plans/${id}/ask`, { question });
