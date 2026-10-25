# Accessibility & Inclusive Design Review

**Standard Target:** WCAG 2.2 Level AA  
**Theme:** Dark Warm Editorial Studio (High Contrast, Low Distraction)

---

## 1. Accessibility Features Implemented

1. **Skip-to-Content Navigation:**
   - Injected keyboard-accessible anchor at the top of [`frontend/index.html`](frontend/index.html):
     ```html
     <a href="#mainContent" class="skip-to-content">Skip to main content</a>
     ```
   - When focused via `Tab`, it becomes visible with a distinct peach background (`#F0B184`) and dark text.
2. **Screen Reader ARIA Live Regions:**
   - Toast container incorporates `aria-live="polite"` and `aria-atomic="true"`:
     ```html
     <div class="toast-container" id="toastContainer" aria-live="polite" aria-atomic="true"></div>
     ```
   - Asynchronous planning operations, generation completions, and validation errors are announced naturally without disrupting reading order.
3. **Contrast Ratios:**
   - Background: Dark Espresso (`#11100F`, `#1B1815`)
   - Text Primary: Warm Cream (`#F1E2CF`) -> **Contrast ratio > 12:1** (Exceeds WCAG AAA requirement of 7:1)
   - Secondary Text: `#B9A895` -> **Contrast ratio > 6.5:1** (Exceeds WCAG AA requirement of 4.5:1)
   - Highlight Accent: `#F0B184` on `#11100F` -> **Contrast ratio > 7.8:1**
4. **Non-Color Reliance:**
   - Overdue tasks display explicit uppercase text badges (`OVERDUE`) in addition to color markers.
   - Over-budget warnings display an exclamation icon alongside clear descriptive text.
5. **Keyboard Navigation & Visible Focus:**
   - All interactive controls (buttons, inputs, checkboxes) maintain visible outline rings with `rgba(240, 177, 132, 0.4)` on `:focus`.
   - Modals and forms are fully navigable via standard `Tab`, `Shift+Tab`, and `Enter`.
6. **Low-Distraction Mode:**
   - All animations respect `@media (prefers-reduced-motion: reduce)`. Decorative spinners and floating mascot animations are disabled when reduced motion is preferred by the operating system.
