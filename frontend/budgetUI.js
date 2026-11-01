// budgetUI.js – DOM rendering for the Budget Guard panel
// ---------------------------------------------------------
// This module reads the current plan from the centralized store and
// updates the budget‑related UI elements. It also installs a debounced
// input listener for the cost fields.

import { getState, setState } from "./store.js";
import { totalEstimated, utilizationPct, remainingBalance, progressClass } from "./budgetUtils.js";
import { debounce } from "./debounce.js";

// Cache of previously rendered values to avoid unnecessary DOM writes
let prevRender = {};

/** Render the Budget Guard UI */
export function renderBudgetGuard() {
  const { currentPlan } = getState();
  if (!currentPlan) return;

  const curr = currentPlan.currency;
  const targetBudget = Number(currentPlan.total_budget);
  const totalEst = totalEstimated(currentPlan.budget_items);
  const utilPct = utilizationPct(targetBudget, totalEst);
  const remaining = remainingBalance(targetBudget, totalEst);

  // ----- Update KPI displays (only when changed) -----
  const setIfChanged = (elId, value) => {
    const el = document.getElementById(elId);
    if (!el) return;
    if (prevRender[elId] !== value) {
      el.textContent = value;
      prevRender[elId] = value;
    }
  };

  setIfChanged('bgTargetBudget', `${curr} ${targetBudget.toLocaleString()}`);
  setIfChanged('bgPlannedSpend', `${curr} ${totalEst.toLocaleString()}`);
  setIfChanged('bgRemainingBalance', `${curr} ${remaining.toLocaleString()}`);

  const remainingEl = document.getElementById('bgRemainingBalance');
  if (remainingEl) {
    const color = remaining < 0 ? 'var(--danger)' : 'var(--text-accent)';
    if (remainingEl.style.color !== color) remainingEl.style.color = color;
  }

  setIfChanged('bgUtilizationPct', `${utilPct}%`);

  // Progress bar
  const fill = document.getElementById('bgProgressFill');
  if (fill) {
    const width = `${Math.min(utilPct, 100)}%`;
    if (fill.style.width !== width) fill.style.width = width;
    const cls = progressClass(utilPct);
    if (fill.className !== cls) fill.className = cls;
  }

  // Over‑budget banner
  const warningBanner = document.getElementById('bgOverBudgetWarning');
  if (warningBanner) {
    const display = totalEst > targetBudget ? 'flex' : 'none';
    if (warningBanner.style.display !== display) warningBanner.style.display = display;
  }

  // ----- Render Budget Items Table -----
  const tbody = document.getElementById('budgetTableBody');
  if (!tbody) return;
  // Re‑build table rows – this is cheap for the typical small number of rows.
  tbody.innerHTML = '';
  (currentPlan.budget_items || []).forEach((item, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${escapeHtml(item.category)}</strong></td>
      <td>${escapeHtml(item.item_name)}</td>
      <td>
        <input 
          type="number" 
          class="table-input budget-cost-input" 
          data-index="${idx}" 
          value="${item.estimated_cost}" 
          min="0" 
          step="50"
        >
      </td>
      <td style="color: var(--text-muted); font-size: 0.8rem;">
        ${escapeHtml(item.notes || '—')}
      </td>
      <td class="no-print">
        <button class="btn btn-outline btn-sm" onclick="app.removeBudgetItem(${idx})" title="Delete item">
          <i data-lucide="trash-2" style="width:14px; height:14px; color:var(--danger);"></i>
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Attach debounced listeners – one per render (lightweight because the handler is debounced)
  const inputs = document.querySelectorAll('.budget-cost-input');
  const handleInput = debounce((e) => {
    const idx = parseInt(e.target.getAttribute('data-index'), 10);
    const val = parseFloat(e.target.value) || 0;
    // Update store state immutably
    setState(state => {
      const plan = { ...state.currentPlan };
      const items = plan.budget_items.map((it, i) => i === idx ? { ...it, estimated_cost: val } : it);
      plan.budget_items = items;
      // Trigger a re‑render of the budget UI
      renderBudgetGuard();
      return { currentPlan: plan };
    });
  }, 300);

  inputs.forEach(input => {
    // Remove any existing listeners by cloning the node (simpler than tracking) – ensures idempotence
    const clone = input.cloneNode(true);
    input.parentNode.replaceChild(clone, input);
    clone.addEventListener('input', handleInput);
  });

  // Refresh Lucide icons
  if (window.lucide) window.lucide.createIcons();
}

/** Simple HTML escaper used in the original code */
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Export for potential external use
export default {
  renderBudgetGuard,
};
