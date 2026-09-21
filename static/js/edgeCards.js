import { el, formatBytes, formatPercent } from './utils.js';

const grid = document.getElementById('edge-grid');

function buildFileChip(file) {
  const chip = el('span', `file-chip${file.is_stale ? ' is-stale' : ''}`, file.name);
  chip.title = file.is_stale
    ? `${file.name} — cached v${file.version}, origin has moved on`
    : `${file.name} — v${file.version}, ${formatBytes(file.size_bytes)}`;
  return chip;
}

function buildCard(edge) {
  const card = el('article', 'edge-card');
  card.id = `edge-card-${edge.name}`;

  const head = el('div', 'edge-card-head', [
    el('span', 'edge-card-name', edge.name),
    el('span', 'status-pill', [el('span', 'status-dot status-dot--hit'), 'Online']),
  ]);

  const latencyRow = el('div', 'edge-metric-row', [
    el('span', 'edge-metric-label', 'Base latency'),
    el('span', 'edge-metric-value', `${edge.base_latency_ms} ms`),
  ]);

  const requestsRow = el('div', 'edge-metric-row', [
    el('span', 'edge-metric-label', 'Requests served'),
    el('span', 'edge-metric-value', String(edge.requests_served)),
  ]);

  const cacheRow = el('div', 'edge-metric-row', [
    el('span', 'edge-metric-label', 'Cache usage'),
    el('span', 'edge-metric-value', `${formatPercent(edge.cache_utilization)} · ${formatBytes(edge.cache_used_bytes)}`),
  ]);

  const cacheTrack = el('div', 'edge-cache-track', [
    el('div', 'edge-cache-fill'),
  ]);
  cacheTrack.firstChild.style.width = `${Math.min(edge.cache_utilization * 100, 100)}%`;

  const filesLabel = el('span', 'edge-files-label', `Stored files (${edge.files.length})`);
  const chips = edge.files.length
    ? el('div', 'edge-file-chips', edge.files.map(buildFileChip))
    : el('p', 'edge-empty-note', 'Nothing cached yet.');

  card.append(head, latencyRow, requestsRow, cacheRow, cacheTrack, filesLabel, chips);

  if (edge.files.some((file) => file.is_stale)) {
    card.classList.add('pulse-stale');
  }

  return card;
}

export function renderEdges(edges) {
  if (!grid) return;
  grid.replaceChildren(...edges.map(buildCard));
}
