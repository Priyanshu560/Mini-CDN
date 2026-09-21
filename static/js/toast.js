const toastEl = document.getElementById('toast');
let hideTimer = null;

export function showToast(message, { isError = false, duration = 3200 } = {}) {
  if (!toastEl) return;
  toastEl.textContent = message;
  toastEl.classList.toggle('is-error', isError);
  toastEl.classList.add('is-visible');

  if (hideTimer) clearTimeout(hideTimer);
  hideTimer = setTimeout(() => {
    toastEl.classList.remove('is-visible');
  }, duration);
}
