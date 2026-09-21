const BASE = '/api';

async function call(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
  } catch (networkError) {
    throw new Error('Could not reach the MiniCDN server. Is app.py running?');
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || `Request to ${path} failed (${response.status})`);
  }
  return data;
}

export const api = {
  getMeta: () => call('/meta'),
  getFiles: () => call('/files'),
  updateFile: (fileName) => call(`/files/${encodeURIComponent(fileName)}/update`, { method: 'POST' }),
  getEdges: () => call('/edges'),
  getAnalytics: () => call('/analytics'),
  submitRequest: (payload) => call('/request', { method: 'POST', body: JSON.stringify(payload) }),
};
