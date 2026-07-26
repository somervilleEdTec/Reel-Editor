import { post } from "../../api.js";
import { state, setState } from "../../store.js";
import { toast } from "../../components/toast.js";

export function mountInspector(el, { copy, flashSaved }) {
  const p = state.project;
  const presets = state.presets || {};
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
      <label class="field" style="flex-direction:row;align-items:center;gap:.5rem">
        <input type="checkbox" class="cap-up" ${p.captions.uppercase ? "checked" : ""} />
        ${copy.uppercase}
      </label>
      <label class="field">${copy.maxWords}
        <input type="number" min="1" max="6" class="cap-mw" value="${p.captions.max_words_visible}" />
      </label>
    </div>`;

  el.querySelectorAll("[data-bg]").forEach((btn) => {
    btn.onclick = async () => {
      try {
        await post("/layers", { background: btn.dataset.bg });
        state.project.layers.background = btn.dataset.bg;
        setState({ project: state.project });
        flashSaved();
        mountInspector(el, { copy, flashSaved });
      } catch (e) {
        toast(String(e.message || e), "danger");
      }
    };
  });

  const sw = el.querySelector(".swatches");
  for (const [name, style] of Object.entries(presets)) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = `swatch${p.captions.preset === name ? " active" : ""}`;
    b.textContent = name;
    b.style.background = style.box || "#333";
    b.style.fontStyle = style.italic ? "italic" : "normal";
    b.onclick = async () => {
      try {
        await post("/captions", { preset: name });
        state.project.captions.preset = name;
        setState({ project: state.project });
        flashSaved();
        mountInspector(el, { copy, flashSaved });
      } catch (e) {
        toast(String(e.message || e), "danger");
      }
    };
    sw.appendChild(b);
  }

  el.querySelector(".cap-y").onchange = async (e) => {
    const y = Number(e.target.value);
    await saveCaptions({ y }, flashSaved);
    document.querySelector(".caption")?.style && (document.querySelector(".caption").style.top = `${y * 100}%`);
  };
  el.querySelector(".cap-up").onchange = async (e) => {
    await saveCaptions({ uppercase: e.target.checked }, flashSaved);
  };
  el.querySelector(".cap-mw").onchange = async (e) => {
    await saveCaptions({ max_words_visible: Number(e.target.value) }, flashSaved);
  };
}

async function saveCaptions(patch, flashSaved) {
  try {
    await post("/captions", patch);
    Object.assign(state.project.captions, patch);
    setState({ project: state.project });
    flashSaved();
  } catch (e) {
    toast(String(e.message || e), "danger");
  }
}
