// timelineUtils.js – pure utility functions for timeline task handling
// ---------------------------------------------------------------
// All functions are pure, deterministic and unit‑testable. They never touch the DOM.

/** Parse a local YYYY‑MM‑DD string into a Date using the local timezone */
function parseLocalDate(str) {
  const [y, m, d] = str.split('-').map(Number);
  return new Date(y, m - 1, d);
}

/** Compute due date (YYYY‑MM‑DD) based on the event date and days before */
export function computeDueDate(eventDateStr, daysBefore) {
  const eventDt = parseLocalDate(eventDateStr);
  if (isNaN(eventDt)) return null;
  const due = new Date(eventDt);
  due.setDate(due.getDate() - daysBefore);
  const yyyy = due.getFullYear();
  const mm = String(due.getMonth() + 1).padStart(2, '0');
  const dd = String(due.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

/** Determine phase label based on days before the event */
export function computePhase(daysBefore) {
  if (daysBefore === 0) return 'Day of Event';
  if (daysBefore <= 3) return 'Final Days';
  if (daysBefore <= 7) return '1 Week Before';
  if (daysBefore <= 14) return '2 Weeks Before';
  return '1 Month Before';
}

/** Generate a stable unique task ID */
function generateTaskId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return `task-${crypto.randomUUID()}`;
  }
  return `task-${Date.now()}-${Math.floor(Math.random() * 1e6)}`;
}

/** Build a full task object from a raw definition */
export function buildTask(raw, eventDateStr) {
  const daysBefore = Number(raw.days_before) || 0;
  const dueDate = computeDueDate(eventDateStr, daysBefore);
  const todayStr = new Date().toISOString().split('T')[0];
  const isOverdue = dueDate && dueDate < todayStr && !raw.completed;
  return {
    id: raw.id || generateTaskId(),
    title: raw.title?.trim() ?? '',
    description: raw.description?.trim() ?? '',
    phase: raw.phase || computePhase(daysBefore),
    due_date: dueDate,
    days_before_event: daysBefore,
    priority: raw.priority || 'medium',
    completed: !!raw.completed,
    is_overdue: isOverdue,
  };
}

/** Sort tasks by due_date (ascending). Missing dates are placed last. */
export function sortTasks(tasks) {
  return tasks.slice().sort((a, b) => {
    if (!a.due_date) return 1;
    if (!b.due_date) return -1;
    return a.due_date.localeCompare(b.due_date);
  });
}

/** Add a new task (already built) and return a new sorted array */
export function addTask(tasks, task) {
  return sortTasks([...tasks, task]);
}

/** Remove a task by its unique ID */
export function removeTaskById(tasks, id) {
  const filtered = tasks.filter(t => t.id !== id);
  return sortTasks(filtered);
}

/** Toggle completion for a task by its unique ID and recompute overdue flag */
export function toggleTaskCompletionById(tasks, id) {
  const todayStr = new Date().toISOString().split('T')[0];
  const newTasks = tasks.map(t => {
    if (t.id !== id) return t;
    const completed = !t.completed;
    const is_overdue = t.due_date && t.due_date < todayStr && !completed;
    return { ...t, completed, is_overdue };
  });
  return sortTasks(newTasks);
}

/** Legacy index‑based helpers kept for backward compatibility */
export function removeTask(tasks, idx) {
  if (idx < 0 || idx >= tasks.length) return tasks;
  const filtered = tasks.filter((_, i) => i !== idx);
  return sortTasks(filtered);
}

export function toggleTaskCompletion(tasks, idx) {
  const todayStr = new Date().toISOString().split('T')[0];
  const newTasks = tasks.map((t, i) => {
    if (i !== idx) return t;
    const completed = !t.completed;
    const is_overdue = t.due_date && t.due_date < todayStr && !completed;
    return { ...t, completed, is_overdue };
  });
  return sortTasks(newTasks);
}
