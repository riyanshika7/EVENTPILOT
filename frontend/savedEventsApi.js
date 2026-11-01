// savedEventsApi.js – thin wrapper around backend persistence for EventPilot plans
// ---------------------------------------------------------------
// All functions return a Promise that resolves to the JSON payload (or throws).
// No UI side‑effects (toast, DOM) are performed here – callers handle those.

/** Helper to build the full API base URL – mirrors EventPilotApp.getApiBaseUrl() */
function getBaseUrl(getApiBaseUrl) {
  // `getApiBaseUrl` is a function injected by the caller (app instance) that returns the base URL without trailing slash.
  return getApiBaseUrl();
}

/** Save the current plan (POST /api/events). */
export async function savePlan(plan, getApiBaseUrl) {
  const res = await fetch(`${getBaseUrl(getApiBaseUrl)}/api/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(plan),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

/** Load all saved plans (GET /api/events). */
export async function loadPlans(getApiBaseUrl) {
  const res = await fetch(`${getBaseUrl(getApiBaseUrl)}/api/events`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

/** Delete a saved plan (DELETE /api/events/:id). */
export async function deletePlan(eventId, getApiBaseUrl) {
  const res = await fetch(`${getBaseUrl(getApiBaseUrl)}/api/events/${eventId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return true; // success flag – callers may ignore the value.
}

/** Load a single plan (GET /api/events/:id). */
export async function loadPlan(eventId, getApiBaseUrl) {
  const res = await fetch(`${getBaseUrl(getApiBaseUrl)}/api/events/${eventId}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}
