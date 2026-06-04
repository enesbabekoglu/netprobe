const state = {
  samples: [],
  charts: [],
  busy: false,
  samplesKey: "",
  chartsKey: "",
  eventsKey: "",
  socket: null,
  reconnectTimer: null,
  lastWsMessageAt: 0
};

const $ = (id) => document.getElementById(id);

function setBusy(value, label = "Calisiyor") {
  state.busy = value;
  $("busyText").textContent = value ? label : "Hazir";
  document.querySelectorAll("button[data-action]").forEach((button) => {
    button.disabled = value;
  });
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatNumber(value, digits = 3) {
  const number = Number(value || 0);
  return number.toFixed(digits);
}

function renderSamples(samples) {
  const key = JSON.stringify(samples.map((sample) => [sample.name, sample.size]));
  if (key === state.samplesKey) return;
  state.samplesKey = key;
  const select = $("sample");
  const current = select.value;
  select.innerHTML = samples.map((sample) => (
    `<option value="${sample.name}">${sample.name} (${formatBytes(sample.size)})${sample.kind === "uploaded" ? " · yuklenen" : ""}</option>`
  )).join("");
  if (current) select.value = current;
}

function renderEvents(events) {
  $("eventCount").textContent = `${events.length} olay`;
  const body = $("eventBody");
  const key = JSON.stringify(events.slice(-80).map((event) => [
    event.timestamp || "",
    event.role || "",
    event.event || "",
    event.sequence ?? "",
    event.session_id || ""
  ]));
  if (key === state.eventsKey) return;
  state.eventsKey = key;
  if (!events.length) {
    body.innerHTML = `<tr class="border-t border-neutral-200">
      <td colspan="4" class="px-3 py-6 text-center text-sm text-neutral-500">Henuz olay yok. Transfer Baslat'a bastiginizda packet_sent, ack_received ve transfer_completed olaylari burada gorunur.</td>
    </tr>`;
    return;
  }
  body.innerHTML = events.slice().reverse().slice(0, 80).map((event) => {
    const detail = [
      event.packet_type,
      event.sequence !== undefined ? `seq=${event.sequence}` : "",
      event.session_id ? `sid=${String(event.session_id).slice(0, 8)}` : "",
      event.message || event.reason || ""
    ].filter(Boolean).join(" · ");
    return `<tr class="border-t border-neutral-200">
      <td class="whitespace-nowrap px-3 py-2 text-xs text-neutral-500">${event.timestamp || ""}</td>
      <td class="px-3 py-2 text-xs font-semibold text-neutral-950">${event.role || ""}</td>
      <td class="px-3 py-2 text-xs text-neutral-800">${event.event || ""}</td>
      <td class="px-3 py-2 text-xs text-neutral-500">${detail}</td>
    </tr>`;
  }).join("");
}

function renderCharts(charts) {
  const key = JSON.stringify(charts.map((chart) => [chart.name, chart.mtime || ""]));
  if (key === state.chartsKey) return;
  state.chartsKey = key;
  const grid = $("chartGrid");
  if (!charts.length) {
    grid.innerHTML = `<div class="rounded-md border border-dashed border-neutral-300 p-6 text-sm text-neutral-500">Henuz grafik yok. Deneyleri calistirip analiz uretin.</div>`;
    return;
  }
  grid.innerHTML = charts.map((chart) => (
    `<figure class="np-card overflow-hidden">
      <img src="${chart.url}${chart.mtime ? `?v=${chart.mtime}` : ""}" alt="${chart.name}" class="w-full bg-white">
      <figcaption class="border-t border-neutral-200 px-3 py-2 text-xs text-neutral-500">${chart.name}</figcaption>
    </figure>`
  )).join("");
}

function renderServer(server) {
  $("serverStatus").textContent = server.running ? `UDP ${server.host}:${server.port}` : "Kapali";
}

function renderResult(result) {
  if (!result) return;
  $("statusMetric").textContent = result.status;
  $("goodputMetric").textContent = `${formatNumber(result.goodput_mbps)} Mbps`;
  $("timeMetric").textContent = `${formatNumber(result.completion_time, 4)} s`;
  $("retryMetric").textContent = String(result.retransmissions);
  $("hashMetric").textContent = result.sha256 ? `${result.sha256.slice(0, 16)}...` : "-";
  $("lastMessage").textContent = result.message || "";
}

async function refreshStatus() {
  const response = await fetch("/api/status");
  const data = await response.json();
  applyStatus(data);
}

function applyStatus(data) {
  state.samples = data.samples || [];
  state.charts = data.charts || [];
  renderSamples(state.samples);
  renderEvents(data.events || []);
  renderCharts(state.charts);
  renderServer(data.server || {});
  $("reportLink").href = "/docs/rapor-taslagi.md";
}

function setStreamStatus(label, active = false) {
  const node = $("streamStatus");
  node.textContent = label;
  node.className = active
    ? "rounded-md border border-neutral-950 bg-neutral-950 px-3 py-2 font-semibold text-white"
    : "rounded-md border border-neutral-300 px-3 py-2 font-semibold text-neutral-900";
}

function connectEventStream() {
  if (state.socket && state.socket.readyState === WebSocket.OPEN) return;
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws/events`);
  state.socket = socket;
  setStreamStatus("WS baglaniyor");

  socket.addEventListener("open", () => {
    setStreamStatus("WS canli", true);
  });

  socket.addEventListener("message", (event) => {
    state.lastWsMessageAt = Date.now();
    const message = JSON.parse(event.data);
    if (message.type === "status") {
      applyStatus(message.payload || {});
    }
  });

  socket.addEventListener("close", () => {
    setStreamStatus("WS koptu");
    if (state.reconnectTimer) clearTimeout(state.reconnectTimer);
    state.reconnectTimer = setTimeout(connectEventStream, 1500);
  });

  socket.addEventListener("error", () => {
    setStreamStatus("WS hata");
    socket.close();
  });
}

async function runTransfer() {
  setBusy(true, "Transfer calisiyor");
  try {
    const payload = {
      sample: $("sample").value,
      payload_size: Number($("payloadSize").value),
      timeout: Number($("timeout").value),
      max_retries: Number($("maxRetries").value),
      window_size: Number($("windowSize").value),
      loss_rate: Number($("lossRate").value),
      delay_ms: Number($("delayMs").value)
    };
    const response = await fetch("/api/transfer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    renderResult(data.result);
    await refreshStatus();
  } finally {
    setBusy(false);
  }
}

async function uploadFile() {
  const input = $("uploadFile");
  if (!input.files.length) {
    $("lastMessage").textContent = "Once bir dosya sec.";
    return;
  }
  setBusy(true, "Dosya yukleniyor");
  try {
    const form = new FormData();
    form.append("file", input.files[0]);
    const response = await fetch("/api/upload", {
      method: "POST",
      body: form
    });
    const data = await response.json();
    if (!data.ok) {
      $("lastMessage").textContent = data.message || "Dosya yuklenemedi";
      return;
    }
    $("lastMessage").textContent = `${data.file.name} listeye eklendi. Simdi Transfer Baslat'a bas.`;
    await refreshStatus();
    $("sample").value = data.file.name;
    input.value = "";
  } finally {
    setBusy(false);
  }
}

async function runExperiments() {
  setBusy(true, "Deneyler calisiyor");
  try {
    await fetch("/api/experiments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: $("profile").value })
    });
    await refreshStatus();
  } finally {
    setBusy(false);
  }
}

async function buildAnalysis() {
  setBusy(true, "Analiz uretiliyor");
  try {
    await fetch("/api/analysis", { method: "POST" });
    await refreshStatus();
  } finally {
    setBusy(false);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  $("transferButton").addEventListener("click", runTransfer);
  $("uploadButton").addEventListener("click", uploadFile);
  $("experimentButton").addEventListener("click", runExperiments);
  $("analysisButton").addEventListener("click", buildAnalysis);
  refreshStatus();
  connectEventStream();
  setInterval(() => {
    if (!state.socket || state.socket.readyState !== WebSocket.OPEN || Date.now() - state.lastWsMessageAt > 2500) {
      refreshStatus();
    }
  }, 1500);
});
