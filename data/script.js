/* ============================================================
   MiniCDN dashboard — client logic
   Talks to the Flask API defined in app.py:
     GET  /files
     GET  /distances/<location>
     GET  /analytics
     POST /request
   Everything here is same-origin fetch(); no build step, no deps.
   ============================================================ */
(() => {
  "use strict";

  // These mirror config.py — EDGE_SERVERS and CLIENT_CITIES are fixed
  // topology, not exposed by an endpoint, so they're declared once here.
  const EDGE_SERVERS = ["Delhi", "Mumbai", "Bangalore"];
  const CLIENT_LOCATIONS = [
    "Delhi", "Mumbai", "Bangalore", "Punjab", "Jaipur",
    "Lucknow", "Kolkata", "Hyderabad", "Ahmedabad",
  ];

  const NODE_POS = {
    client: { x: 60, y: 130 },
    router: { x: 232, y: 130 },
    Delhi: { x: 490, y: 50 },
    Mumbai: { x: 490, y: 130 },
    Bangalore: { x: 490, y: 210 },
    origin: { x: 760, y: 130 },
  };

  const EDGE_NODE_ID = { Delhi: "edge-node-delhi", Mumbai: "edge-node-mumbai", Bangalore: "edge-node-bangalore" };
  const LINK_ROUTER_EDGE_ID = { Delhi: "link-router-delhi", Mumbai: "link-router-mumbai", Bangalore: "link-router-bangalore" };
  const LINK_EDGE_ORIGIN_ID = { Delhi: "link-delhi-origin", Mumbai: "link-mumbai-origin", Bangalore: "link-bangalore-origin" };

  const GAUGE_CIRCUMFERENCE = 327; // matches stroke-dasharray on .gauge-value in style.css

  const el = (id) => document.getElementById(id);

  let lastDistances = {};
  let lastRequestsPerServer = {};

  /* ---------- fetch helper ---------- */

  async function api(path, opts) {
    const res = await fetch(path, opts);
    const isJson = (res.headers.get("content-type") || "").includes("application/json");
    const data = isJson ? await res.json() : null;
    if (!res.ok) {
      throw new Error((data && data.error) || `Request failed (${res.status})`);
    }
    return data;
  }

  function setApiStatus(online) {
    el("api-status-dot").classList.toggle("is-online", online);
    el("api-status-dot").classList.toggle("is-offline", !online);
    el("api-status-text").textContent = online ? "API connected" : "API unreachable";
    el("connection-banner").hidden = online;
  }

  /* ---------- setup: dropdowns ---------- */

  function populateLocationSelects() {
    const locationSelect = el("input-location");
    const distanceSelect = el("distance-location-select");
    CLIENT_LOCATIONS.forEach((city) => {
      locationSelect.add(new Option(city, city));
      distanceSelect.add(new Option(city, city));
    });
  }

  async function populateFileSelect() {
    const fileSelect = el("input-file");
    try {
      const data = await api("/files");
      fileSelect.innerHTML = "";
      (data.files || []).forEach((name) => fileSelect.add(new Option(name, name)));
      if (!fileSelect.options.length) {
        fileSelect.add(new Option("No files on origin", ""));
      }
    } catch {
      fileSelect.innerHTML = "";
      fileSelect.add(new Option("Unavailable — check API", ""));
    }
  }

  /* ---------- edge status + cards ---------- */

  // No endpoint reports real edge health, so status is derived from each
  // edge's share of recent traffic: no traffic yet reads as idle, a heavy
  // skew toward one edge reads as degraded (overloaded), otherwise healthy.
  function edgeStatus(name) {
    const total = EDGE_SERVERS.reduce((sum, n) => sum + (lastRequestsPerServer[n] || 0), 0);
    const count = lastRequestsPerServer[name] || 0;
    if (total === 0) return { label: "Idle", cls: "idle", count };
    const share = count / total;
    return share > 0.55
      ? { label: "Degraded", cls: "degraded", count }
      : { label: "Healthy", cls: "healthy", count };
  }

  function renderEdgeCards() {
    const wrap = el("edge-cards");
    wrap.innerHTML = "";
    const maxCount = Math.max(1, ...EDGE_SERVERS.map((n) => lastRequestsPerServer[n] || 0));

    EDGE_SERVERS.forEach((name) => {
      const status = edgeStatus(name);
      const distance = lastDistances[name];

      const card = document.createElement("div");
      card.className = `edge-card status-${status.cls}`;
      card.innerHTML = `
        <span class="edge-card-dot"></span>
        <div class="edge-card-main">
          <div class="edge-card-title-row">
            <span class="edge-card-name">${name}</span>
            <span class="edge-card-status">${status.label}</span>
          </div>
          <div class="edge-card-load-track">
            <div class="edge-card-load-fill" style="width:${Math.round((status.count / maxCount) * 100)}%"></div>
          </div>
        </div>
        <div class="edge-card-distance">${distance != null ? distance.toFixed(1) : "—"}<small>${distance != null ? "km away" : "pick a city"}</small></div>
      `;
      wrap.appendChild(card);

      const svgNode = el(EDGE_NODE_ID[name]);
      svgNode.classList.remove("status-healthy", "status-degraded", "status-idle");
      svgNode.classList.add(`status-${status.cls}`);
    });
  }

  async function refreshDistances() {
    const location = el("distance-location-select").value;
    if (!location) return;
    try {
      lastDistances = await api(`/distances/${encodeURIComponent(location)}`);
    } catch {
      lastDistances = {};
    }
    renderEdgeCards();
  }

  /* ---------- analytics ---------- */

  function renderLoadBars() {
    const wrap = el("server-load-bars");
    wrap.innerHTML = "";
    const maxCount = Math.max(1, ...EDGE_SERVERS.map((n) => lastRequestsPerServer[n] || 0));

    EDGE_SERVERS.forEach((name) => {
      const count = lastRequestsPerServer[name] || 0;
      const row = document.createElement("div");
      row.className = "load-bar-row";
      row.innerHTML = `
        <span>${name}</span>
        <span class="load-bar-track"><span class="load-bar-fill" style="width:${Math.round((count / maxCount) * 100)}%"></span></span>
        <span class="load-bar-count">${count}</span>
      `;
      wrap.appendChild(row);
    });
  }

  async function refreshAnalytics(opts = {}) {
    let data;
    try {
      data = await api("/analytics");
    } catch {
      if (!opts.silent) setApiStatus(false);
      return;
    }
    setApiStatus(true);

    el("kpi-total").textContent = data.total_requests ?? "0";
    el("kpi-hit-ratio").textContent = `${Math.round((data.hit_ratio || 0) * 100)}%`;
    el("kpi-avg-latency").textContent = data.average_latency_ms != null ? `${data.average_latency_ms} ms` : "—";
    el("kpi-failed").textContent = data.failed_requests ?? "0";

    const ratio = data.hit_ratio || 0;
    el("gauge-circle").style.strokeDashoffset = String(GAUGE_CIRCUMFERENCE * (1 - ratio));
    el("gauge-percent").textContent = `${Math.round(ratio * 100)}%`;
    el("analytics-hits").textContent = data.cache_hits ?? 0;
    el("analytics-misses").textContent = data.cache_misses ?? 0;

    el("stat-avg-latency").textContent = data.average_latency_ms != null ? `${data.average_latency_ms} ms` : "—";
    el("stat-median-latency").textContent = data.median_latency_ms != null ? `${data.median_latency_ms} ms` : "—";
    el("stat-fastest-latency").textContent = data.fastest_request_ms != null ? `${data.fastest_request_ms} ms` : "—";
    el("stat-slowest-latency").textContent = data.slowest_request_ms != null ? `${data.slowest_request_ms} ms` : "—";

    el("most-requested-file").textContent = data.most_requested_file
      ? `${data.most_requested_file} — ${data.most_requested_file_count} request${data.most_requested_file_count === 1 ? "" : "s"}`
      : "No requests yet";

    lastRequestsPerServer = data.requests_per_server || {};
    renderLoadBars();
    renderEdgeCards();
  }

  /* ---------- routing diagram animation ---------- */

  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function animateSegment(from, to, duration) {
    const pulse = el("request-pulse");
    pulse.setAttribute("opacity", "1");
    return new Promise((resolve) => {
      const start = performance.now();
      function frame(now) {
        const t = Math.min(1, (now - start) / duration);
        const e = easeInOutCubic(t);
        pulse.setAttribute("cx", from.x + (to.x - from.x) * e);
        pulse.setAttribute("cy", from.y + (to.y - from.y) * e);
        if (t < 1) requestAnimationFrame(frame);
        else resolve();
      }
      requestAnimationFrame(frame);
    });
  }

  function setLinkActive(id, active) {
    const link = el(id);
    if (link) link.classList.toggle("link-active", active);
  }

  async function playRouteAnimation(edgeName, cacheStatus) {
    if (!EDGE_NODE_ID[edgeName]) return;
    document.querySelectorAll(".link").forEach((l) => l.classList.remove("link-active"));
    document.querySelectorAll(".node-edge").forEach((n) => n.classList.remove("pulse-hit", "pulse-miss"));

    setLinkActive("link-client-router", true);
    await animateSegment(NODE_POS.client, NODE_POS.router, 260);

    setLinkActive(LINK_ROUTER_EDGE_ID[edgeName], true);
    await animateSegment(NODE_POS.router, NODE_POS[edgeName], 320);

    const isMiss = cacheStatus === "MISS" || cacheStatus === "STALE";
    if (isMiss) {
      setLinkActive(LINK_EDGE_ORIGIN_ID[edgeName], true);
      await animateSegment(NODE_POS[edgeName], NODE_POS.origin, 300);
      await animateSegment(NODE_POS.origin, NODE_POS[edgeName], 300);
    }

    el("request-pulse").setAttribute("opacity", "0");
    const edgeNode = el(EDGE_NODE_ID[edgeName]);
    edgeNode.classList.add(isMiss ? "pulse-miss" : "pulse-hit");
    setTimeout(() => edgeNode.classList.remove("pulse-hit", "pulse-miss"), 1600);
  }

  /* ---------- simulate request form ---------- */

  function describeFailure(status) {
    switch (status) {
      case "NETWORK_FAILURE":
        return "Simulated network failure — the request never reached the edge. Try again.";
      case "FILE_NOT_FOUND":
        return "That file isn't on the origin server.";
      case "INVALID_LOCATION":
        return "That location isn't one the simulator recognizes.";
      default:
        return "The request failed.";
    }
  }

  function showHeroResult(result, clientName, location, fileName) {
    el("hero-result").hidden = false;
    el("hero-caption").textContent = `Last request: ${clientName} in ${location} asked for ${fileName}.`;

    el("result-edge").textContent = result.server_selected;

    const cacheChip = el("result-cache");
    cacheChip.textContent = result.cache_status;
    cacheChip.className = "result-chip " + (result.cache_status === "HIT" ? "chip-hit" : "chip-miss");

    el("result-latency").textContent = `${result.latency_ms} ms`;
  }

  async function handleSimulateSubmit(event) {
    event.preventDefault();
    const submitBtn = el("simulate-submit");
    const feedback = el("simulate-feedback");
    const clientName = el("input-client-name").value.trim() || "Anonymous";
    const location = el("input-location").value;
    const fileName = el("input-file").value;

    if (!location || !fileName) {
      feedback.textContent = "Pick a location and a file first.";
      feedback.className = "form-feedback is-error";
      return;
    }

    submitBtn.disabled = true;
    feedback.textContent = "Sending request…";
    feedback.className = "form-feedback";

    try {
      const result = await api("/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ client_name: clientName, location, file_name: fileName }),
      });

      if (result.status !== "SUCCESS") {
        feedback.textContent = describeFailure(result.status);
        feedback.className = "form-feedback is-error";
      } else {
        feedback.textContent = `Served by ${result.server_selected} in ${result.latency_ms} ms.`;
        feedback.className = "form-feedback is-success";
        showHeroResult(result, clientName, location, fileName);
        await playRouteAnimation(result.server_selected, result.cache_status);
      }
      refreshAnalytics();
    } catch (err) {
      feedback.textContent = err.message || "Something went wrong.";
      feedback.className = "form-feedback is-error";
      setApiStatus(false);
    } finally {
      submitBtn.disabled = false;
    }
  }

  /* ---------- init ---------- */

  async function init() {
    el("api-base-display").textContent = window.location.origin || "this origin";
    populateLocationSelects();
    el("distance-location-select").value = CLIENT_LOCATIONS[0];

    el("simulate-form").addEventListener("submit", handleSimulateSubmit);
    el("distance-location-select").addEventListener("change", refreshDistances);
    el("refresh-analytics").addEventListener("click", () => refreshAnalytics());

    await populateFileSelect();
    await Promise.all([refreshDistances(), refreshAnalytics()]);

    setInterval(() => refreshAnalytics({ silent: true }), 15000);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
