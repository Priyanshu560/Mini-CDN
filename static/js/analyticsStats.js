import { formatMs, formatPercent } from './utils.js';

const hitRatioEl = document.getElementById('stat-hit-ratio');
const avgLatencyEl = document.getElementById('stat-avg-latency');
const totalRequestsEl = document.getElementById('stat-total-requests');
const mostUsedEl = document.getElementById('stat-most-used');

export function renderAnalyticsStats(analytics) {
  const servedCount = (analytics.cache_hits || 0) + (analytics.cache_misses || 0);

  hitRatioEl.textContent = servedCount ? formatPercent(analytics.hit_ratio) : '—';
  avgLatencyEl.textContent = servedCount ? formatMs(analytics.average_latency_ms) : '—';
  totalRequestsEl.textContent = String(analytics.total_requests || 0);
  mostUsedEl.textContent = analytics.most_used_server || '—';
}
