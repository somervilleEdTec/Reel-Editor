import { post } from "../../api.js";
import { state, setState } from "../../store.js";
import { toast } from "../../components/toast.js";
import { paintCaption } from "./caption_preview.js";

export function mountStage(el, { copy, flashSaved }) {
  const project = state.project;
  const zones = state.safezones || {};
  el.innerHTML = `<div class="stage-well settle">
      <div class="stage">
        <video class="stage-video" muted playsinline controls loop preload="metadata"
          src="/media/source?v=${encodeURIComponent(state.projectPath || "")}"></video>
        <div class="safe" hidden></div>
        <div class="inset"><span class="inset-handle" title="Drag to resize"></span></div>
        <div class="caption"></div>
      </div>
    </div>
    <div class="stage-controls">
      <label><input type="checkbox" class="sz-toggle" /> ${copy.safezones}</label>
      <select class="sz-platform">
        ${Object.keys(zones).map((k) => `<option value="${k}">${k}</option>`).join("")}
      </select>
    </div>`;

  const stage = el.querySelector(".stage");
  const inset = el.querySelector(".inset");
  const handle = el.querySelector(".inset-handle");
  const caption = el.querySelector(".caption");
  const safe = el.querySelector(".safe");
  const video = el.querySelector(".stage-video");

  video.addEventListener("error", () => {
    toast("Could not load video preview — check the source file path", "danger");
  });

  function applyLayout() {
    const p = state.project;
    inset.style.left = `${p.layers.inset.x * 100}%`;
    inset.style.top = `${p.layers.inset.y * 100}%`;
    inset.style.width = `${p.layers.inset.w * 100}%`;
    paintCaption(caption, p, state.presets || {});
  }
  applyLayout();
  el._refreshStage = applyLayout;

  wireSafezones(el, safe, zones);
  wireInsetMove(stage, inset, flashSaved);
  wireInsetResize(stage, inset, handle, flashSaved);
  wireCaptionDrag(stage, caption, flashSaved);

  el.querySelector(".stage-well").addEventListener(
    "animationend",
    (e) => e.currentTarget.classList.remove("settle"),
    { once: true },
  );
}

function wireSafezones(el, safe, zones) {
  const toggle = el.querySelector(".sz-toggle");
  const platform = el.querySelector(".sz-platform");
  const paintSafe = () => {
    const z = zones[platform.value];
    if (!toggle.checked || !z) {
      safe.hidden = true;
      return;
    }
    safe.hidden = false;
    safe.style.borderTop = `${(z.top || 0) * 100}% solid rgba(196,92,38,.25)`;
    safe.style.borderBottom = `${(z.bottom || 0) * 100}% solid rgba(196,92,38,.25)`;
    safe.style.borderRight = `${(z.right || 0) * 100}% solid rgba(196,92,38,.2)`;
    safe.style.borderLeft = `${(z.left || 0) * 100}% solid rgba(196,92,38,.2)`;
  };
  toggle.onchange = paintSafe;
  platform.onchange = paintSafe;
}

function wireInsetMove(stage, inset, flashSaved) {
  let dragging = false;
  inset.addEventListener("pointerdown", (e) => {
    if (e.target.classList.contains("inset-handle")) return;
    dragging = true;
    inset.setPointerCapture(e.pointerId);
  });
  inset.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const r = stage.getBoundingClientRect();
    inset.style.left = `${clamp01((e.clientX - r.left) / r.width) * 100}%`;
    inset.style.top = `${clamp01((e.clientY - r.top) / r.height) * 100}%`;
  });
  inset.addEventListener("pointerup", async () => {
    if (!dragging) return;
    dragging = false;
    await saveInset(stage, inset, flashSaved);
  });
}

function wireInsetResize(stage, inset, handle, flashSaved) {
  let resizing = false;
  handle.addEventListener("pointerdown", (e) => {
    e.stopPropagation();
    resizing = true;
    handle.setPointerCapture(e.pointerId);
  });
  handle.addEventListener("pointermove", (e) => {
    if (!resizing) return;
    const r = stage.getBoundingClientRect();
    const ir = inset.getBoundingClientRect();
    const w = clamp((e.clientX - ir.left) / r.width, 0.15, 0.95);
    inset.style.width = `${w * 100}%`;
  });
  handle.addEventListener("pointerup", async () => {
    if (!resizing) return;
    resizing = false;
    await saveInset(stage, inset, flashSaved, true);
  });
}

function wireCaptionDrag(stage, caption, flashSaved) {
  let capDrag = false;
  caption.addEventListener("pointerdown", (e) => {
    capDrag = true;
    caption.setPointerCapture(e.pointerId);
  });
  caption.addEventListener("pointermove", (e) => {
    if (!capDrag) return;
    const r = stage.getBoundingClientRect();
    caption.style.top = `${clamp01((e.clientY - r.top) / r.height) * 100}%`;
  });
  caption.addEventListener("pointerup", async () => {
    if (!capDrag) return;
    capDrag = false;
    const r = stage.getBoundingClientRect();
    const y = clamp01((caption.getBoundingClientRect().top - r.top) / r.height);
    try {
      await post("/captions", { y });
      state.project.captions.y = y;
      setState({ project: state.project });
      flashSaved();
    } catch (err) {
      toast(String(err.message || err), "danger");
    }
  });
}

async function saveInset(stage, inset, flashSaved, withWidth = false) {
  const r = stage.getBoundingClientRect();
  const ir = inset.getBoundingClientRect();
  const patch = {
    x: clamp01((ir.left - r.left) / r.width),
    y: clamp01((ir.top - r.top) / r.height),
  };
  if (withWidth) patch.w = clamp(ir.width / r.width, 0.15, 0.95);
  try {
    await post("/layers", { inset: patch });
    Object.assign(state.project.layers.inset, patch);
    setState({ project: state.project });
    flashSaved();
  } catch (err) {
    toast(String(err.message || err), "danger");
  }
}

const clamp01 = (n) => clamp(n, 0, 1);
const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
