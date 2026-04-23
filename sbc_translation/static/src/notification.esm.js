/**
 * Simple notification helper using Bootstrap alerts.
 * Replaces Odoo's `notification` service in the portal/frontend context.
 *
 * Usage:
 *   import { showNotification } from "../notification";
 *   showNotification("Letter saved", "success");
 */

const AUTO_DISMISS_MS = {
  success: 3000,
  info: 4000,
  warning: 5000,
  danger: 6000,
};

/** @type {HTMLElement|null} */
let _container = null;

/**
 * Get (or lazily create) the fixed notification container.
 * @returns {HTMLElement}
 */
function _getContainer() {
  if (!_container || !document.body.contains(_container)) {
    _container = document.createElement("div");
    _container.style.cssText =
      "position:fixed;top:1rem;right:1rem;z-index:99999;" +
      "display:flex;flex-direction:column;gap:0.5rem;min-width:260px;max-width:420px;";
    document.body.appendChild(_container);
  }
  return _container;
}

/**
 * Show a dismissible Bootstrap alert notification.
 * @param {String} message  - plain text or safe HTML
 * @param {'success'|'info'|'warning'|'danger'} [type='info']
 */
export function showNotification(message, type = "info") {
  const container = _getContainer();

  const el = document.createElement("div");
  el.className = `alert alert-${type} alert-dismissible fade show shadow-sm mb-0`;
  el.setAttribute("role", "alert");
  el.innerHTML = `
        <span>${message}</span>
        <button type="button" class="btn-close" aria-label="Close"></button>
    `;

  // Manual close button
  function _dismiss(_el) {
    _el.classList.remove("show");
    setTimeout(() => _el.remove(), 300);
  }
  el.querySelector(".btn-close").addEventListener("click", () => _dismiss(el));

  container.appendChild(el);

  // Auto-dismiss
  const delay = AUTO_DISMISS_MS[type] ?? 4000;
  setTimeout(() => _dismiss(el), delay);
}

export default showNotification;
