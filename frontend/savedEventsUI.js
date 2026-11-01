// savedEventsUI.js – rendering logic for saved events and dashboard
// ---------------------------------------------------------------
// This module provides functions to render saved‑event cards and the recent events
// list on the dashboard. It removes inline `onclick` handlers and instead uses
// delegated event handling via `data-action` and `data-id` attributes.
// All dynamic values are escaped using the `escapeHtml` function from
// `app.js` (imported lazily to avoid circular dependencies).

export function renderSavedEventsGrid(events, callbacks = {}) {
  const grid = document.getElementById('savedEventsGrid');
  const empty = document.getElementById('savedEmptyState');
  if (!grid) return;

  if (!events || events.length === 0) {
    grid.style.display = 'none';
    if (empty) empty.style.display = 'block';
    return;
  }

  grid.style.display = 'grid';
  if (empty) empty.style.display = 'none';
  grid.innerHTML = '';

  events.forEach(evt => {
    grid.appendChild(createEventCardElement(evt));
  });

  // Ensure delegated listeners are attached only once
  attachSavedEventsDelegatedHandlers(grid, callbacks);

  if (window.lucide) window.lucide.createIcons();
}

export function renderDashboardRecentGrid(events) {
  const grid = document.getElementById('dashboardEventsList');
  const empty = document.getElementById('dashboardEmptyState');
  if (!grid) return;

  if (!events || events.length === 0) {
    grid.style.display = 'none';
    if (empty) empty.style.display = 'block';
    return;
  }

  grid.style.display = 'grid';
  if (empty) empty.style.display = 'none';
  grid.innerHTML = '';

  const recent = events.slice(0, 3);
  recent.forEach(evt => grid.appendChild(createEventCardElement(evt)));

  if (window.lucide) window.lucide.createIcons();
}

// Helper that creates a card element for a single event.
function createEventCardElement(evt) {
  import { escapeHtml } from './htmlUtils.js';

  const safeTitle = escapeHtml(evt.name || 'Untitled');
  const safeDate = escapeHtml(evt.event_date || '');
  const safeBudget = escapeHtml(evt.total_budget?.toString() ?? '0');
  const safeId = String(evt.id).replace(/[^a-zA-Z0-9_-]/g, ''); // simple sanitisation

  const card = document.createElement('div');
  card.className = 'saved-event-card';
  card.dataset.id = safeId;
  // Use data-action to indicate which button was pressed
  card.innerHTML = `
    <div class="card-header">
      <h4 class="event-title">${safeTitle}</h4>
      <div class="event-meta">
        <span class="event-date">${safeDate}</span>
        <span class="event-budget">₹${safeBudget}</span>
      </div>
    </div>
    <div class="card-actions">
      <button class="btn btn-sm" data-action="view" title="View">View</button>
      <button class="btn btn-sm btn-danger" data-action="delete" title="Delete">Delete</button>
    </div>
  `;
  return card;
}

// Attach delegated click handling to a container. Called once per container.
function attachSavedEventsDelegatedHandlers(container, callbacks) {
  // Always store the latest callbacks on the container
  container.__savedEventsCallbacks = callbacks;
  // If the listener is already attached, nothing more to do
  if (container.__savedEventsHandlersAttached) return;
  container.addEventListener('click', e => {
    const btn = e.target.closest('button[data-action]');
    if (!btn) return;
    const action = btn.dataset.action;
    const card = btn.closest('[data-id]');
    if (!card) return;
    const id = card.dataset.id;
    // Validate ID
    if (!/^[a-zA-Z0-9_-]+$/.test(id)) {
      console.warn('Invalid event ID encountered:', id);
      return;
    }
    const currentCallbacks = container.__savedEventsCallbacks || {};
    if (action === 'view' && typeof currentCallbacks.onView === 'function') {
      currentCallbacks.onView(id);
    } else if (action === 'delete' && typeof currentCallbacks.onDelete === 'function') {
      currentCallbacks.onDelete(id);
    }
  });
  container.__savedEventsHandlersAttached = true;
}

// Export the internal helper for testing purposes.
export { createEventCardElement, attachSavedEventsDelegatedHandlers };
