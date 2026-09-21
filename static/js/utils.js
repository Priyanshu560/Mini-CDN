export function formatMs(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return `${value.toFixed(1)} ms`;
}

export function formatBytes(bytes) {
  if (bytes === null || bytes === undefined) return '—';
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let i = 0;
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024;
    i += 1;
  }
  return i === 0 ? `${size} B` : `${size.toFixed(1)} ${units[i]}`;
}

export function formatPercent(fraction) {
  if (fraction === null || fraction === undefined) return '—';
  return `${(fraction * 100).toFixed(0)}%`;
}

export function formatClock(isoString) {
  const date = new Date(isoString);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function el(tag, className, children) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (children) {
    (Array.isArray(children) ? children : [children]).forEach((child) => {
      if (child === null || child === undefined) return;
      node.append(child instanceof Node ? child : document.createTextNode(String(child)));
    });
  }
  return node;
}
