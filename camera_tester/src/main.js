import "./styles.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
const LIVE_ENDPOINT = `${API_BASE_URL}/api/detections/live-detect-frame/`;

const state = {
  stream: null,
  devices: [],
  live: false,
  busy: false,
  liveTimer: null,
  latestDetections: [],
  lastAddedAt: new Map(),
};

const offscreenCanvas = document.createElement("canvas");

document.querySelector("#app").innerHTML = `
  <main class="app-shell">
    <header class="topbar">
      <a class="brand" href="/">
        <span class="brand-mark">KA</span>
        <span>
          <strong>Kitunga Live YOLO</strong>
          <small>Iriun Webcam realtime detection</small>
        </span>
      </a>
      <div id="connectionStatus" class="status-pill">camera idle</div>
    </header>

    <section class="workspace">
      <section class="video-panel">
        <div class="video-frame">
          <video id="video" autoplay playsinline muted></video>
          <canvas id="overlay"></canvas>
          <div id="emptyVideo" class="empty-video">
            <strong>Aucun flux actif</strong>
            <span>Demarre Iriun sur le telephone et le PC, puis choisis la camera.</span>
          </div>
        </div>
      </section>

      <aside class="control-panel">
        <div class="field">
          <label for="cameraSelect">Camera</label>
          <select id="cameraSelect"></select>
        </div>

        <div class="button-grid">
          <button id="refreshDevices" class="secondary-button" type="button">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 12a8 8 0 1 1-2.34-5.66"/><path d="M20 4v6h-6"/></svg>
            Detecter
          </button>
          <button id="startCamera" class="primary-button" type="button">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 10l4.5-2.6v9.2L15 14"/><rect x="3" y="6" width="12" height="12" rx="2"/></svg>
            Ouvrir
          </button>
          <button id="liveYolo" class="primary-button wide-button" type="button" disabled>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 4v16"/><path d="M18 4v16"/><path d="M8 6h8v12H8z"/></svg>
            Lancer YOLO live
          </button>
        </div>

        <div class="field">
          <label for="deviceId">Device ID</label>
          <input id="deviceId" value="IRIUN-PC-TEST" />
        </div>

        <div class="field">
          <label for="basketCode">Basket code</label>
          <input id="basketCode" value="SB-001" />
        </div>

        <div class="settings-grid">
          <div class="field">
            <label for="minConfidence">Seuil YOLO</label>
            <input id="minConfidence" type="number" min="0.05" max="1" step="0.05" value="0.25" />
          </div>
          <div class="field">
            <label for="addCooldown">Cooldown panier</label>
            <input id="addCooldown" type="number" min="1" max="30" step="1" value="5" />
          </div>
        </div>

        <label class="toggle-row">
          <input id="autoBasket" type="checkbox" checked />
          <span>Ajouter automatiquement au panier</span>
        </label>

        <section class="result-panel">
          <span class="section-label">Detections live</span>
          <div id="lastResult" class="result-copy">Aucune detection lancee.</div>
        </section>
      </aside>
    </section>

    <section class="log-panel">
      <div class="panel-title">
        <span class="section-label">Journal</span>
        <button id="clearLog" class="text-button" type="button">Effacer</button>
      </div>
      <ol id="logs"></ol>
    </section>
  </main>
`;

const video = document.querySelector("#video");
const overlay = document.querySelector("#overlay");
const emptyVideo = document.querySelector("#emptyVideo");
const cameraSelect = document.querySelector("#cameraSelect");
const connectionStatus = document.querySelector("#connectionStatus");
const lastResult = document.querySelector("#lastResult");
const logs = document.querySelector("#logs");
const liveButton = document.querySelector("#liveYolo");

function log(message, level = "info") {
  const item = document.createElement("li");
  item.className = `log-${level}`;
  item.textContent = `${new Date().toLocaleTimeString("fr-FR")} - ${message}`;
  logs.prepend(item);
}

function setStatus(text, mode = "idle") {
  connectionStatus.textContent = text;
  connectionStatus.dataset.mode = mode;
}

function setCameraEnabled(enabled) {
  liveButton.disabled = !enabled;
  emptyVideo.classList.toggle("hidden", enabled);
}

function readNumber(selector, fallback) {
  const rawValue = document.querySelector(selector).value || "";
  const parsed = Number(rawValue.replace(",", "."));
  return Number.isFinite(parsed) ? parsed : fallback;
}

async function enumerateCameras() {
  const devices = await navigator.mediaDevices.enumerateDevices();
  state.devices = devices.filter((device) => device.kind === "videoinput");

  cameraSelect.innerHTML = "";
  state.devices.forEach((device, index) => {
    const option = document.createElement("option");
    option.value = device.deviceId;
    option.textContent = device.label || `Camera ${index + 1}`;
    cameraSelect.appendChild(option);
  });

  const iriun = state.devices.find((device) => device.label.toLowerCase().includes("iriun"));
  if (iriun) {
    cameraSelect.value = iriun.deviceId;
    log(`Iriun detecte: ${iriun.label}`, "success");
  } else if (state.devices[0]) {
    cameraSelect.value = state.devices[0].deviceId;
  }

  log(`${state.devices.length} camera(s) disponible(s).`);
}

async function requestPermissionThenList() {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("getUserMedia indisponible. Utilise Chrome/Edge sur localhost.");
  }
  const tempStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
  tempStream.getTracks().forEach((track) => track.stop());
  await enumerateCameras();
}

async function startCamera() {
  stopLiveDetection();
  if (state.stream) {
    state.stream.getTracks().forEach((track) => track.stop());
  }

  const constraints = {
    video: {
      deviceId: cameraSelect.value ? { exact: cameraSelect.value } : undefined,
      width: { ideal: 1280 },
      height: { ideal: 720 },
    },
    audio: false,
  };

  state.stream = await navigator.mediaDevices.getUserMedia(constraints);
  video.srcObject = state.stream;
  await video.play();
  resizeOverlay();
  setCameraEnabled(true);
  setStatus("camera active", "ok");
  log("Flux camera ouvert.", "success");
}

function resizeOverlay() {
  const rect = video.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  overlay.width = Math.max(1, Math.round(rect.width * dpr));
  overlay.height = Math.max(1, Math.round(rect.height * dpr));
  overlay.style.width = `${rect.width}px`;
  overlay.style.height = `${rect.height}px`;
  const context = overlay.getContext("2d");
  context.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function captureFrameBlob() {
  const sourceWidth = video.videoWidth || 1280;
  const sourceHeight = video.videoHeight || 720;
  const width = Math.min(800, sourceWidth);
  const height = Math.round(width * (sourceHeight / sourceWidth));
  offscreenCanvas.width = width;
  offscreenCanvas.height = height;
  offscreenCanvas.getContext("2d").drawImage(video, 0, 0, width, height);

  return new Promise((resolve) => {
    offscreenCanvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.65);
  });
}

async function detectLiveFrame() {
  if (!state.stream || state.busy || !state.live) return;
  state.busy = true;

  try {
    const blob = await captureFrameBlob();
    if (!blob) throw new Error("Frame video impossible a capturer.");

    const form = new FormData();
    form.append("device_id", document.querySelector("#deviceId").value || "IRIUN-PC-TEST");
    form.append("min_confidence", String(readNumber("#minConfidence", 0.25)));
    form.append("image", blob, `live_${Date.now()}.jpg`);

    const response = await fetch(LIVE_ENDPOINT, {
      method: "POST",
      body: form,
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Detection live refusee par Django.");

    state.latestDetections = payload.detections || [];
    drawDetections(state.latestDetections);
    renderDetectionResult(state.latestDetections);
    await maybeAddDetectionsToBasket(state.latestDetections);
    setStatus(`${state.latestDetections.length} objet(s)`, state.latestDetections.length ? "ok" : "idle");
  } catch (error) {
    setStatus("live error", "error");
    log(error.message, "error");
  } finally {
    state.busy = false;
  }
}

function drawDetections(detections) {
  resizeOverlay();
  const context = overlay.getContext("2d");
  const rect = video.getBoundingClientRect();
  context.clearRect(0, 0, rect.width, rect.height);

  const videoWidth = video.videoWidth || rect.width;
  const videoHeight = video.videoHeight || rect.height;
  const scale = Math.min(rect.width / videoWidth, rect.height / videoHeight);
  const drawWidth = videoWidth * scale;
  const drawHeight = videoHeight * scale;
  const offsetX = (rect.width - drawWidth) / 2;
  const offsetY = (rect.height - drawHeight) / 2;

  detections.forEach((detection, index) => {
    if (!detection.box) return;
    const x = offsetX + detection.box.x1 * drawWidth;
    const y = offsetY + detection.box.y1 * drawHeight;
    const width = (detection.box.x2 - detection.box.x1) * drawWidth;
    const height = (detection.box.y2 - detection.box.y1) * drawHeight;
    const label = `${detection.label} ${(detection.confidence * 100).toFixed(0)}%`;

    context.strokeStyle = index === 0 ? "oklch(70% 0.16 166)" : "oklch(66% 0.12 72)";
    context.lineWidth = 3;
    context.strokeRect(x, y, width, height);

    context.font = "700 14px Segoe UI, system-ui, sans-serif";
    const labelWidth = context.measureText(label).width + 16;
    const labelHeight = 26;
    context.fillStyle = "oklch(17% 0.018 170 / 0.86)";
    context.fillRect(x, Math.max(0, y - labelHeight), labelWidth, labelHeight);
    context.fillStyle = "oklch(98% 0.008 170)";
    context.fillText(label, x + 8, Math.max(18, y - 8));
  });
}

function renderDetectionResult(detections) {
  if (!detections.length) {
    lastResult.textContent = "Aucun objet detecte.";
    return;
  }

  lastResult.textContent = detections
    .map((detection) => {
      const raw = detection.raw_label ? ` raw=${detection.raw_label}` : "";
      return `${detection.label} confidence=${detection.confidence}${raw}`;
    })
    .join("\n");
}

async function maybeAddDetectionsToBasket(detections) {
  if (!document.querySelector("#autoBasket").checked) return;

  const threshold = readNumber("#minConfidence", 0.25);
  const cooldownMs = readNumber("#addCooldown", 5) * 1000;
  const now = Date.now();
  const basketCode = document.querySelector("#basketCode").value || "SB-001";
  const deviceId = document.querySelector("#deviceId").value || "IRIUN-PC-TEST";

  for (const detection of detections) {
    if (!detection.label || detection.confidence < threshold) continue;
    const previous = state.lastAddedAt.get(detection.label) || 0;
    if (now - previous < cooldownMs) continue;

    const added = await addDetectionToBasket({
      basketCode,
      deviceId,
      label: detection.label,
      confidence: detection.confidence,
    });
    if (added) {
      state.lastAddedAt.set(detection.label, now);
    }
  }
}

async function addDetectionToBasket({ basketCode, deviceId, label, confidence }) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/baskets/${basketCode}/add-detection/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        device_id: deviceId,
        detected_label: label,
        confidence: Math.round(confidence * 100) / 100,
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Ajout panier refuse.");
    log(`Panier: ${label} -> ${payload.detection_status}`, payload.detection_status === "accepted" ? "success" : "info");
    return true;
  } catch (error) {
    log(`Panier: ${label} non ajoute (${error.message})`, "error");
    return false;
  }
}

function startLiveDetection() {
  if (!state.stream) return;
  state.live = true;
  liveButton.classList.add("is-active");
  liveButton.innerHTML = liveButton.innerHTML.replace("Lancer YOLO live", "Arreter YOLO live");
  log("YOLO live demarre.");

  const loop = async () => {
    if (!state.live) return;
    await detectLiveFrame();
    state.liveTimer = window.setTimeout(loop, 650);
  };
  loop();
}

function stopLiveDetection() {
  state.live = false;
  if (state.liveTimer) {
    window.clearTimeout(state.liveTimer);
    state.liveTimer = null;
  }
  liveButton.classList.remove("is-active");
  liveButton.innerHTML = liveButton.innerHTML.replace("Arreter YOLO live", "Lancer YOLO live");
  drawDetections([]);
}

function toggleLiveDetection() {
  if (state.live) {
    stopLiveDetection();
    log("YOLO live arrete.");
  } else {
    startLiveDetection();
  }
}

cameraSelect.addEventListener("change", () => {
  stopLiveDetection();
});

document.querySelector("#refreshDevices").addEventListener("click", async () => {
  try {
    await requestPermissionThenList();
  } catch (error) {
    setStatus("permission error", "error");
    log(error.message, "error");
  }
});

document.querySelector("#startCamera").addEventListener("click", async () => {
  try {
    if (!state.devices.length) await requestPermissionThenList();
    await startCamera();
  } catch (error) {
    setStatus("camera error", "error");
    setCameraEnabled(false);
    log(error.message, "error");
  }
});

liveButton.addEventListener("click", toggleLiveDetection);
document.querySelector("#clearLog").addEventListener("click", () => {
  logs.innerHTML = "";
});
window.addEventListener("resize", () => drawDetections(state.latestDetections));

requestPermissionThenList().catch((error) => {
  setStatus("camera idle", "idle");
  log(error.message, "error");
});
