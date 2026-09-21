import { el, formatBytes } from './utils.js';

const list = document.getElementById('origin-file-list');

const EXTENSION_LABEL = {
  html: 'HTML',
  css: 'CSS',
  js: 'JS',
  json: 'JSON',
  png: 'PNG',
  jpg: 'JPG',
  jpeg: 'JPG',
  ico: 'ICO',
  mp4: 'MP4',
};

function kindLabel(fileName) {
  const extension = fileName.split('.').pop().toLowerCase();
  return EXTENSION_LABEL[extension] || extension.slice(0, 4).toUpperCase();
}

function buildRow(file, onUpdate) {
  const row = el('li');
  row.id = `origin-row-${file.name}`;

  const name = el('div', 'origin-file-name', [
    el('span', 'origin-file-icon', kindLabel(file.name)),
    el('span', null, file.name),
  ]);

  const version = el('span', 'version-badge', `v${file.version}`);
  version.id = `version-badge-${file.name}`;

  const size = el('span', 'origin-file-size', formatBytes(file.size_bytes));

  const button = el('button', 'btn btn--small', 'Update');
  button.type = 'button';
  button.addEventListener('click', async () => {
    button.disabled = true;
    button.textContent = 'Publishing…';
    try {
      await onUpdate(file.name);
    } finally {
      button.disabled = false;
      button.textContent = 'Update';
    }
  });

  row.append(name, version, size, button);
  return row;
}

export function renderOriginFiles(files, { onUpdate }) {
  if (!list) return;
  list.replaceChildren(...files.map((file) => buildRow(file, onUpdate)));
}

export function flashVersionBump(fileName) {
  const badge = document.getElementById(`version-badge-${fileName}`);
  if (!badge) return;
  badge.classList.add('just-updated');
  setTimeout(() => badge.classList.remove('just-updated'), 900);
}
