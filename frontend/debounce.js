// debounce.js – reusable debounce helper
// -------------------------------------------------
// Usage: const debounced = debounce(fn, 300);
// The returned function will invoke `fn` after `wait` ms have elapsed
// since the last call.

export function debounce(fn, wait) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), wait);
  };
}
