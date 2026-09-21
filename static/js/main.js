import { api } from './api.js';
import { initRequestForm, refreshFileOptions } from './requestForm.js';
import { renderEdges } from './edgeCards.js';
import { renderPerformance } from './performance.js';
import { renderAnalyticsStats } from './analyticsStats.js';
import { renderOriginFiles, flashVersionBump } from './originExplorer.js';
import { addTimelineEntry } from './timeline.js';
import { showToast } from './toast.js';

async function refreshEdgesAndAnalytics() {
  const [edgesData, analytics] = await Promise.all([api.getEdges(), api.getAnalytics()]);
  renderEdges(edgesData.edges);
  renderPerformance(analytics);
  renderAnalyticsStats(analytics);
}

async function refreshOriginFiles() {
  const filesData = await api.getFiles();
  renderOriginFiles(filesData.files, { onUpdate: handleFileUpdate });
  refreshFileOptions(filesData.files);
  return filesData.files;
}

async function handleFileUpdate(fileName) {
  try {
    const updated = await api.updateFile(fileName);
    flashVersionBump(fileName);
    showToast(`${fileName} published as v${updated.version}. Edges holding the old copy are now stale.`);
    await Promise.all([refreshOriginFiles(), refreshEdgesAndAnalytics()]);
  } catch (error) {
    showToast(error.message, { isError: true });
  }
}

async function bootstrap() {
  try {
    const [meta, filesData, edgesData, analytics] = await Promise.all([
      api.getMeta(),
      api.getFiles(),
      api.getEdges(),
      api.getAnalytics(),
    ]);

    renderOriginFiles(filesData.files, { onUpdate: handleFileUpdate });
    renderEdges(edgesData.edges);
    renderPerformance(analytics);
    renderAnalyticsStats(analytics);

    initRequestForm({
      meta,
      files: filesData.files,
      onResolved: async (record) => {
        addTimelineEntry(record);
        await refreshEdgesAndAnalytics();
      },
    });
  } catch (error) {
    showToast(error.message, { isError: true, duration: 6000 });
  }
}

bootstrap();
