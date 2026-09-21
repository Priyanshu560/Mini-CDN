import { el, formatClock, formatMs } from './utils.js';

const list = document.getElementById('timeline-list');
const emptyState = document.getElementById('timeline-empty');
const MAX_ENTRIES = 40;

function arrow() {
  return el('span', 'timeline-arrow', '→');
}

function node(label, tone) {
  return el('span', `timeline-node${tone ? ` is-${tone}` : ''}`, label);
}

function buildPath(record) {
  const parts = [node(record.client_name || 'Client')];

  if (!record.server_selected) {
    parts.push(arrow(), node('rejected', 'fail'));
    return parts;
  }

  parts.push(arrow(), node(record.server_selected));

  if (record.status === 'NETWORK_FAILURE') {
    parts.push(arrow(), node('network failure', 'fail'));
    return parts;
  }

  if (record.cache_status === 'HIT') {
    parts.push(arrow(), node('cache hit', 'hit'));
  } else {
    parts.push(arrow(), node(record.cache_status === 'STALE' ? 'stale' : 'cache miss', 'miss'));
    parts.push(arrow(), node('origin'));
  }

  return parts;
}

export function addTimelineEntry(record) {
  if (!list) return;
  if (emptyState) emptyState.remove();

  const item = el('li', 'timeline-item', [
    el('span', 'timeline-time', formatClock(record.timestamp)),
    el('div', 'timeline-path', buildPath(record)),
    el('span', 'timeline-latency', record.status === 'SUCCESS' ? formatMs(record.latency_ms) : record.status.replace(/_/g, ' ')),
  ]);

  list.prepend(item);

  while (list.children.length > MAX_ENTRIES) {
    list.removeChild(list.lastElementChild);
  }
}
