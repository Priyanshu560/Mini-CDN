import { wait } from './utils.js';

const packet = document.getElementById('packet');

const wires = {
  clientRouter: document.getElementById('wire-client-router'),
  toEdge: {
    Delhi: document.getElementById('wire-router-delhi'),
    Mumbai: document.getElementById('wire-router-mumbai'),
    Bangalore: document.getElementById('wire-router-bangalore'),
  },
  toOrigin: {
    Delhi: document.getElementById('wire-delhi-origin'),
    Mumbai: document.getElementById('wire-mumbai-origin'),
    Bangalore: document.getElementById('wire-bangalore-origin'),
  },
};

const nodes = {
  client: document.getElementById('node-client'),
  router: document.getElementById('node-router'),
  origin: document.getElementById('node-origin'),
  edges: {
    Delhi: document.getElementById('node-edge-Delhi'),
    Mumbai: document.getElementById('node-edge-Mumbai'),
    Bangalore: document.getElementById('node-edge-Bangalore'),
  },
};

const allNodes = [nodes.client, nodes.router, nodes.origin, ...Object.values(nodes.edges)];
const allWires = [wires.clientRouter, ...Object.values(wires.toEdge), ...Object.values(wires.toOrigin)];

const TONE_TO_NODE_CLASS = { flow: 'is-active', hit: 'is-hit', miss: 'is-miss', fail: 'is-fail' };
const TONE_TO_WIRE_CLASS = { flow: 'is-active', hit: 'is-hit', miss: 'is-miss', fail: 'is-fail' };

function clearNode(node) {
  node.classList.remove('is-active', 'is-hit', 'is-miss', 'is-fail', 'is-checking');
}

function clearWire(wire) {
  wire.classList.remove('is-active', 'is-hit', 'is-miss', 'is-fail');
}

function setNodeTone(node, tone) {
  clearNode(node);
  if (tone) node.classList.add(TONE_TO_NODE_CLASS[tone]);
}

export function resetDiagram() {
  allNodes.forEach(clearNode);
  allWires.forEach(clearWire);
  packet.classList.remove('is-hit', 'is-miss', 'is-fail');
  packet.setAttribute('opacity', '0');
  const clientSub = document.getElementById('client-sub-label');
  if (clientSub) clientSub.textContent = 'Not connected';
}

function pointAtFraction(path, fraction) {
  const length = path.getTotalLength();
  return path.getPointAtLength(length * fraction);
}

function travel(path, { tone = 'flow', reverse = false, duration = 550 } = {}) {
  return new Promise((resolve) => {
    clearWire(path);
    path.classList.add(TONE_TO_WIRE_CLASS[tone]);

    packet.classList.remove('is-hit', 'is-miss', 'is-fail');
    if (tone !== 'flow') packet.classList.add(TONE_TO_WIRE_CLASS[tone]);
    packet.setAttribute('opacity', '1');

    const start = performance.now();

    function frame(now) {
      const elapsed = now - start;
      const t = Math.min(elapsed / duration, 1);
      const eased = 1 - (1 - t) ** 3; // ease-out cubic
      const fraction = reverse ? 1 - eased : eased;
      const point = pointAtFraction(path, fraction);
      packet.setAttribute('cx', point.x);
      packet.setAttribute('cy', point.y);
      if (t < 1) {
        requestAnimationFrame(frame);
      } else {
        resolve();
      }
    }
    requestAnimationFrame(frame);
  });
}

/**
 * Plays the full visual story of one resolved request against the
 * diagram: client -> router -> edge -> (origin, on a miss) -> back.
 * `record` is exactly what POST /api/request returns.
 */
export async function animateRequest(record, { onStage } = {}) {
  resetDiagram();
  const say = (text, tone) => onStage && onStage({ text, tone });

  const clientSub = document.getElementById('client-sub-label');
  if (clientSub) clientSub.textContent = record.location || 'Unknown location';

  setNodeTone(nodes.client, 'flow');
  say('Finding nearest edge server…', 'flow');
  await travel(wires.clientRouter, { tone: 'flow', duration: 500 });
  setNodeTone(nodes.router, 'flow');
  await wait(120);

  const server = record.server_selected;

  if (!server) {
    setNodeTone(nodes.router, 'fail');
    say(routerFailureMessage(record.status), 'fail');
    return;
  }

  const edgeWire = wires.toEdge[server];
  const edgeNode = nodes.edges[server];

  say(`Selecting ${server}…`, 'flow');
  await travel(edgeWire, { tone: 'flow', duration: 480 });
  setNodeTone(edgeNode, 'flow');

  if (record.status === 'NETWORK_FAILURE') {
    setNodeTone(edgeNode, 'fail');
    say(`Network failure reaching ${server}. Request dropped.`, 'fail');
    return;
  }

  edgeNode.classList.add('is-checking');
  say('Checking cache…', 'flow');
  await wait(480);
  edgeNode.classList.remove('is-checking');

  if (record.cache_status === 'HIT') {
    setNodeTone(edgeNode, 'hit');
    say('Cache hit — serving response.', 'hit');
    await travel(edgeWire, { tone: 'hit', reverse: true, duration: 460 });
    setNodeTone(nodes.router, 'hit');
    await travel(wires.clientRouter, { tone: 'hit', reverse: true, duration: 460 });
    setNodeTone(nodes.client, 'hit');
    say('Response delivered from the edge.', 'hit');
    return;
  }

  // MISS or STALE both mean: this edge has to go fetch from origin.
  setNodeTone(edgeNode, 'miss');
  const missLabel = record.cache_status === 'STALE' ? 'Cached copy is stale' : 'Cache miss';
  say(`${missLabel} — fetching from origin…`, 'miss');
  const originWire = wires.toOrigin[server];
  await travel(originWire, { tone: 'miss', duration: 520 });
  setNodeTone(nodes.origin, 'miss');
  await wait(280);

  say('Origin sending file back…', 'flow');
  setNodeTone(nodes.origin, 'flow');
  await travel(originWire, { tone: 'flow', reverse: true, duration: 520 });
  setNodeTone(edgeNode, 'hit');
  say('Updating edge cache…', 'hit');
  await wait(260);

  say('Serving response.', 'hit');
  await travel(edgeWire, { tone: 'hit', reverse: true, duration: 460 });
  setNodeTone(nodes.router, 'hit');
  await travel(wires.clientRouter, { tone: 'hit', reverse: true, duration: 460 });
  setNodeTone(nodes.client, 'hit');
  say('Response delivered — edge cache warmed for next time.', 'hit');
}

function routerFailureMessage(status) {
  if (status === 'INVALID_LOCATION') return 'Unknown client location — request rejected.';
  if (status === 'FILE_NOT_FOUND') return 'Requested file does not exist on origin.';
  return 'Request failed before reaching an edge.';
}
