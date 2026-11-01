// store.js – simple centralized state container for EventPilot UI
// ---------------------------------------------------------------
// The store holds the same shape as the original EventPilotApp state
// (currentPlan, savedEvents, modelStatus, etc.).  It provides
// getState(), setState(updater) and a subscription mechanism so UI
// modules can react only to the data they care about.

let state = {
  currentPlan: null,
  savedEvents: [],
  modelStatus: { available: false, model_available: false },
};

const listeners = new Set();

/** Get a shallow copy of the current state */
export function getState() {
  return { ...state };
}

/** Update state via an updater function and notify subscribers */
export function setState(updater) {
  const prev = { ...state };
  const newState = updater({ ...state });
  state = { ...state, ...newState };
  // Notify only if something actually changed (simple shallow compare)
  if (JSON.stringify(prev) !== JSON.stringify(state)) {
    listeners.forEach(fn => fn(state, prev));
  }
}

/** Subscribe to state changes – returns an unsubscribe function */
export function subscribe(fn) {
  listeners.add(fn);
  // Initial call so the subscriber can render immediately
  fn(state, {});
  return () => listeners.delete(fn);
}
