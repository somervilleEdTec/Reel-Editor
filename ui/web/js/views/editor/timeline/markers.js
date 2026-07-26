import { post, get } from "../../../api.js";
import { state, setState } from "../../../store.js";
import { toast } from "../../../components/toast.js";

export function mountMarkers(el, { zoom, flashSaved }) {
  el._zoom = zoom;
  el._flashSaved = flashSaved;
  loadAndRender(el);
}

export function refreshMarkers(el, zoom) {
  if (zoom != null) el._zoom = zoom;
  loadAndRender(el);
}

async function loadAndRender(el) {
  try {
    const data = await get("/markers");
    el._markers = Array.isArray(data) ? data : (data?.markers || []);
  } catch {
    el._markers = state.project?.markers || [];
  }
  renderMarkers(el);
}

function renderMarkers(el) {
  el.innerHTML = "";
  (el._markers || []).forEach((m) => {
    const t = m.time ?? m.output_time ?? 0;
    const pin = document.createElement("div");
    pin.className = "tl-marker";
    pin.style.left = `${t * el._zoom}px`;
    pin.title = m.label || fmtT(t);
    pin.addEventListener("click", (e) => { e.stopPropagation(); });
    el.appendChild(pin);
  });
}

export async function addMarkerAtTime(el, outTime, label = "") {
  try {
    const updated = await post("/markers", { time: outTime, label });
    el._markers = Array.isArray(updated) ? updated : (updated?.markers || [...(el._markers || []), { time: outTime, label }]);
    renderMarkers(el);
    if (updated?.project) setState({ project: updated.project });
    el._flashSaved();
  } catch (err) {
    // Optimistic: add locally even if API fails
    el._markers = [...(el._markers || []), { time: outTime, label }];
    renderMarkers(el);
  }
}

const fmtT = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
