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
    el._markers = data?.markers || [];
  } catch {
    el._markers = state.project?.markers || [];
  }
  renderMarkers(el);
}

function renderMarkers(el) {
  el.innerHTML = "";
  (el._markers || []).forEach((m) => {
    const t = m.t_out_s ?? 0;
    const pin = document.createElement("div");
    pin.className = "tl-marker";
    pin.style.left = `${t * el._zoom}px`;
    pin.title = m.label || fmtT(t);
    pin.addEventListener("click", (e) => e.stopPropagation());
    el.appendChild(pin);
  });
}

export async function addMarkerAtTime(el, outTime, label = "") {
  try {
    const updated = await post("/markers", { t_out_s: outTime, label });
    el._markers = updated?.markers || [];
    renderMarkers(el);
    if (state.project) {
      setState({ project: { ...state.project, markers: el._markers } });
    }
    el._flashSaved?.();
  } catch (err) {
    toast(String(err.message || err), "danger");
  }
}

const fmtT = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
