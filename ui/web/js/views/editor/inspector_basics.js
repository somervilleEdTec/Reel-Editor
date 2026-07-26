import { post } from "../../api.js";
import { setState, state } from "../../store.js";
import { refreshStage, showError } from "./inspector_helpers.js";

export function mountInspectorBasics(el, { copy, flashSaved, rerender }) {
  const p = state.project;
  el.innerHTML = `<div class="cluster">
      <p class="section-label">${copy.background}</p>
      <div class="seg">
        <button type="button" data-bg="media" class="${p.layers.background === "media" ? "active" : ""}">${copy.bgMedia}</button>
        <button type="button" data-bg="camera" class="${p.layers.background === "camera" ? "active" : ""}">${copy.bgCamera}</button>
      </div>
    </div>
    <div class="cluster">
      <p class="section-label">${copy.captions}</p>
      <p class="section-label" style="margin-top:.5rem">${copy.captionStyle}</p>
      <div class="swatches"></div>
      <label class="field">${copy.captionY}
        <input type="range" min="0.2" max="0.9" step="0.01" class="cap-y" value="${p.captions.y}" />
      </label>
      <label class="field inline-check"><input type="checkbox" class="cap-up" ${p.captions.uppercase ? "checked" : ""} /> ${copy.uppercase}</label>
      <label class="field">${copy.maxWords}
        <input type="number" min="1" max="6" class="cap-mw" value="${p.captions.max_words_visible}" />
      </label>
    </div>`;

  el.querySelectorAll("[data-bg]").forEach((btn) => {
    btn.onclick = () => saveLayer(btn.dataset.bg, flashSaved, rerender);
  });
  mountSwatches(el.querySelector(".swatches"), copy, flashSaved, rerender);
  el.querySelector(".cap-y").oninput = (e) => {
    state.project.captions.y = Number(e.target.value);
    refreshStage();
  };
  el.querySelector(".cap-y").onchange = (e) => saveCaptions({ y: Number(e.target.value) }, flashSaved);
  el.querySelector(".cap-up").onchange = (e) => saveCaptions({ uppercase: e.target.checked }, flashSaved);
  el.querySelector(".cap-mw").onchange = (e) => saveCaptions({ max_words_visible: Number(e.target.value) }, flashSaved);
}

function mountSwatches(el, copy, flashSaved, rerender) {
  for (const [name, style] of Object.entries(state.presets || {})) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = `swatch${state.project.captions.preset === name ? " active" : ""}`;
    b.textContent = name;
    b.style.background = style.box || "#333";
    b.style.fontStyle = style.italic ? "italic" : "normal";
    b.onclick = () => savePreset(name, flashSaved, rerender);
    el.appendChild(b);
  }
}

async function saveLayer(background, flashSaved, rerender) {
  try {
    await post("/layers", { background });
    state.project.layers.background = background;
    setState({ project: state.project });
    flashSaved();
    refreshStage();
    rerender();
  } catch (e) {
    showError(e);
  }
}

async function savePreset(preset, flashSaved, rerender) {
  try {
    await post("/captions", { preset });
    state.project.captions.preset = preset;
    setState({ project: state.project });
    flashSaved();
    refreshStage();
    rerender();
  } catch (e) {
    showError(e);
  }
}

async function saveCaptions(patch, flashSaved) {
  try {
    await post("/captions", patch);
    Object.assign(state.project.captions, patch);
    setState({ project: state.project });
    flashSaved();
    refreshStage();
  } catch (e) {
    showError(e);
  }
}
