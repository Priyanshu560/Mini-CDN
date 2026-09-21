import { formatMs } from './utils.js';

const withoutValueEl = document.getElementById('perf-without-value');
const withValueEl = document.getElementById('perf-with-value');
const withoutBarEl = document.getElementById('perf-without-bar');
const withBarEl = document.getElementById('perf-with-bar');
const timeSavedEl = document.getElementById('perf-time-saved');
const improvementEl = document.getElementById('perf-improvement');
const footerEl = document.getElementById('perf-footer');
const emptyNoteEl = document.getElementById('perf-empty-note');

export function renderPerformance(analytics) {
  const servedCount = (analytics.cache_hits || 0) + (analytics.cache_misses || 0);
  const originBaseline = analytics.origin_base_latency_ms;

  withoutValueEl.textContent = formatMs(originBaseline);

  if (servedCount === 0) {
    withBarEl.style.width = '0%';
    withoutBarEl.style.width = '0%';
    withValueEl.textContent = '—';
    footerEl.hidden = true;
    emptyNoteEl.hidden = false;
    return;
  }

  const avgLatency = analytics.average_latency_ms;
  withValueEl.textContent = formatMs(avgLatency);

  const reference = Math.max(originBaseline, avgLatency, 1);
  withoutBarEl.style.width = `${(originBaseline / reference) * 100}%`;
  withBarEl.style.width = `${(avgLatency / reference) * 100}%`;

  const timeSaved = originBaseline - avgLatency;
  const improvement = originBaseline > 0 ? (timeSaved / originBaseline) * 100 : 0;

  timeSavedEl.textContent = formatMs(timeSaved);
  improvementEl.textContent = `${improvement >= 0 ? '' : '−'}${Math.abs(improvement).toFixed(0)}%`;

  footerEl.hidden = false;
  emptyNoteEl.hidden = true;
}
