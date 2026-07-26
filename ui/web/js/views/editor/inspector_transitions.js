import { post } from "../../api.js";
import { setState, state } from "../../store.js";
import { showError } from "./inspector_helpers.js";

export function mountInspectorTransitions(el, { copy, flashSaved }) {
  const exp = state.project.export || {};
  el.innerHTML = `<div class="cluster">
    <p class="section-label">${copy.transitions}</p>
    <div class="seg">
      <button type="button" data-transition="cut" class="${exp.transition === "cut" ? "active" : ""}">${copy.transitionCut}</button>
      <button type="button" data-transition="crossfade" class="${exp.transition === "crossfade" ? "active" : ""}">${copy.transitionCrossfade}</button>
    </div>
    <label class="field">${copy.transitionDuration}
      <input type="number" min="0" step="0.05" class="transition-s" value="${exp.transition_s ?? 0.25}" />
    </label>
  </div>`;

  el.querySelectorAll("[data-transition]").forEach((btn) => {
    btn.onclick = () => saveExport({ transition: btn.dataset.transition }, flashSaved, el);
  });
  el.querySelector(".transition-s").onchange = (e) => {
    saveExport({ transition_s: Number(e.target.value) }, flashSaved, el);
  };
}

async function saveExport(patch, flashSaved, root) {
  try {
    state.project.export = await post("/export-settings", patch);
    setState({ project: state.project });
    root.querySelectorAll("[data-transition]").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.transition === state.project.export.transition);
    });
    flashSaved();
  } catch (e) {
    showError(e);
  }
}
