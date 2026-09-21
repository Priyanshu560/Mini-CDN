import { api } from './api.js';
import { animateRequest } from './diagram.js';
import { el, formatMs } from './utils.js';
import { showToast } from './toast.js';

const form = document.getElementById('request-form');
const locationSelect = document.getElementById('client-location');
const fileSelect = document.getElementById('requested-file');
const nameInput = document.getElementById('client-name');
const submitBtn = document.getElementById('route-request-btn');
const submitLabel = document.getElementById('route-request-label');
const stageLog = document.getElementById('stage-log');
const resultSummary = document.getElementById('result-summary');
const resultServer = document.getElementById('result-server');
const resultCache = document.getElementById('result-cache');
const resultLatency = document.getElementById('result-latency');
const resultDistance = document.getElementById('result-distance');
const diagramStatusDot = document.getElementById('diagram-status-dot');
const diagramStatusText = document.getElementById('diagram-status-text');
const networkSection = document.getElementById('network');

function populateSelect(select, values) {
  select.replaceChildren(...values.map((value) => {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    return option;
  }));
}

function addStageLine(text, tone) {
  const line = el('li', tone ? `stage--${tone}` : '', [el('span', 'stage-dot'), text]);
  stageLog.appendChild(line);
  return line;
}

function setDiagramStatus(text, tone) {
  diagramStatusText.textContent = text;
  diagramStatusDot.className = `diagram-status-dot${tone ? ` is-${tone}` : ''}`;
}

function resultTone(record) {
  if (record.status !== 'SUCCESS') return 'fail';
  if (record.cache_status === 'HIT') return 'hit';
  if (record.cache_status) return 'miss'; // MISS or STALE
  return '';
}

function showResult(record) {
  resultServer.textContent = record.server_selected || '—';
  resultCache.textContent = record.status === 'SUCCESS'
    ? record.cache_status
    : record.status.replace(/_/g, ' ');
  const tone = resultTone(record);
  resultCache.className = `result-value${tone ? ` result-value--${tone}` : ''}`;
  resultLatency.textContent = record.status === 'SUCCESS' ? formatMs(record.latency_ms) : '—';
  resultDistance.textContent = (record.distance_km !== null && record.distance_km !== undefined)
    ? `${record.distance_km} km`
    : '—';
  resultSummary.hidden = false;
}

export function initRequestForm({ meta, files, onResolved }) {
  populateSelect(locationSelect, meta.client_locations);
  populateSelect(fileSelect, files.map((file) => file.name));

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    submitBtn.disabled = true;
    submitLabel.textContent = 'Routing…';
    resultSummary.hidden = true;
    stageLog.innerHTML = '';
    setDiagramStatus('Sending request…', 'flow');
    networkSection.scrollIntoView({ behavior: 'smooth', block: 'center' });

    const payload = {
      client_name: nameInput.value.trim() || 'Anonymous',
      location: locationSelect.value,
      file_name: fileSelect.value,
    };

    try {
      const record = await api.submitRequest(payload);

      await animateRequest(record, {
        onStage: ({ text, tone }) => {
          addStageLine(text, tone);
          setDiagramStatus(text, tone);
        },
      });

      showResult(record);
      if (onResolved) onResolved(record);
    } catch (error) {
      addStageLine(error.message, 'fail');
      setDiagramStatus(error.message, 'fail');
      showToast(error.message, { isError: true });
    } finally {
      submitBtn.disabled = false;
      submitLabel.textContent = 'Route request';
    }
  });
}

export function refreshFileOptions(files) {
  const current = fileSelect.value;
  populateSelect(fileSelect, files.map((file) => file.name));
  if (files.some((file) => file.name === current)) {
    fileSelect.value = current;
  }
}
