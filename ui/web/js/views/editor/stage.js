import { post } from "../../api.js";
import { state, setState } from "../../store.js";
import { toast } from "../../components/toast.js";

export function mountStage(el, { copy, flashSaved }) {
  const project = state.project;
  const zones = state.safezones || {};
  el.innerHTML = `<div class="stage-well settle">
      <div class="stage">
        <div class="safe" hidden></div>
        <div class="inset"></div>
        <div class="caption">CAPTIONS</div>
      </div>
    </div>
    <div class="stage-controls">
      <label><input type="checkbox" class="sz-toggle" /> ${copy.safezones}</label>
      <select class="sz-platform">
        ${Object.keys(zones).map((k) => `<option value="${k}">${k}</option>`).join("")}
      </select>
    </div>`;

  const well = el.querySelector(".stage-well");
  const stage = el.querySelector(".stage");
  const inset = el.querySelector(".inset");
  const caption = el.querySelector(".caption");
  const safe = el.querySelector(".safe");

  function apply() {
    const p = state.project;
    inset.style.left = `${p.layers.inset.x * 100}%`;
    inset.style.top = `${p.layers.inset.y * 100}%`;
    inset.style.width = `${p.layers.inset.w * 100}%`;
    caption.style.top = `${p.captions.y * 100}%`;
    caption.style.textTransform = p.captions.uppercase ? "uppercase" : "none";
  }
  apply();

  const toggle = el.querySelector(".sz-toggle");
  const platform = el.querySelector(".sz-platform");
  function paintSafe() {
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
  }
  toggle.onchange = paintSafe;
  platform.onchange = paintSafe;

  let dragging = false;
  inset.addEventListener("pointerdown", (e) => {
    dragging = true;
    inset.setPointerCapture(e.pointerId);
  });
  inset.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const r = stage.getBoundingClientRect();
    inset.style.left = `${((e.clientX - r.left) / r.width) * 100}%`;
    inset.style.top = `${((e.clientY - r.top) / r.height) * 100}%`;
  });
  inset.addEventListener("pointerup", async () => {
    dragging = false;
    const r = stage.getBoundingClientRect();
    const ir = inset.getBoundingClientRect();
    const x = (ir.left - r.left) / r.width;
    const y = (ir.top - r.top) / r.height;
    try {
      await post("/layers", { inset: { x, y } });
      state.project.layers.inset.x = x;
      state.project.layers.inset.y = y;
      setState({ project: state.project });
      flashSaved();
    } catch (err) {
      toast(String(err.message || err), "danger");
    }
  });

  let capDrag = false;
  caption.addEventListener("pointerdown", (e) => {
    capDrag = true;
    caption.setPointerCapture(e.pointerId);
  });
  caption.addEventListener("pointermove", (e) => {
    if (!capDrag) return;
    const r = stage.getBoundingClientRect();
    const y = (e.clientY - r.top) / r.height;
    caption.style.top = `${y * 100}%`;
  });
  caption.addEventListener("pointerup", async () => {
    if (!capDrag) return;
    capDrag = false;
    const r = stage.getBoundingClientRect();
    const y = (caption.getBoundingClientRect().top - r.top) / r.height;
    try {
      await post("/captions", { y });
      state.project.captions.y = y;
      setState({ project: state.project });
      flashSaved();
    } catch (err) {
      toast(String(err.message || err), "danger");
    }
  });

  // re-settle only once
  well.addEventListener("animationend", () => well.classList.remove("settle"), { once: true });
}
