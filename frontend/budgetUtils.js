// budgetUtils.js – pure calculations for the Budget Guard
// -----------------------------------------------------
// All functions are pure (no DOM access) and can be unit‑tested.

/** Sum of estimated_cost for all budget items */
export function totalEstimated(budgetItems) {
  if (!Array.isArray(budgetItems)) return 0;
  return budgetItems.reduce((sum, itm) => sum + Number(itm.estimated_cost || 0), 0);
}

/** Utilization percentage (targetBudget > 0) */
export function utilizationPct(targetBudget, totalEstimated) {
  if (targetBudget <= 0) return 0;
  return Math.round((totalEstimated / targetBudget) * 100);
}

/** Remaining balance */
export function remainingBalance(targetBudget, totalEstimated) {
  return Math.round((targetBudget - totalEstimated) * 100) / 100;
}

/** Determine progress‑fill CSS class based on utilization */
export function progressClass(utilPct) {
  if (utilPct > 100) return 'editorial-progress-fill danger';
  if (utilPct > 85) return 'editorial-progress-fill warning';
  return 'editorial-progress-fill';
}
