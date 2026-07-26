import { post } from "../../api.js";
import { setState, state } from "../../store.js";
import { showError, sourceLabel } from "./inspector_helpers.js";

export function mountInspectorAudio(el, { copy, flashSaved }) {
  const audio = state.project.audio || {};
  el.innerHTML = `<div class="cluster">
    <p class="section-label">${copy.audio}</p>
    <label class="field">${copy.musicSource}<select class="music-source"></select></label>
    <label class="field">${copy.musicGain}
      <input type="number" class="music-gain" step="0.5" value="${audio.music_gain_db ?? -18}" />
    </label>
    <label class="field inline-check">
      <input type="checkbox" class="duck" ${audio.duck_under_speech ? "checked" : ""} /> ${copy.duckUnderSpeech}
    </label>
  </div>`;

  const select = el.querySelector(".music-source");
  select.appendChild(new Option(copy.noMusicSource, ""));
  for (const src of state.project.sources || []) {
    select.appendChild(new Option(sourceLabel(src), src.id));
  }
  select.value = audio.music_track_id || "";
  select.onchange = () => saveAudio({ music_track_id: select.value || null }, flashSaved);
  el.querySelector(".music-gain").onchange = (e) => {
    saveAudio({ music_gain_db: Number(e.target.value) }, flashSaved);
  };
  el.querySelector(".duck").onchange = (e) => {
    saveAudio({ duck_under_speech: e.target.checked }, flashSaved);
  };
}

async function saveAudio(patch, flashSaved) {
  try {
    state.project.audio = await post("/audio", patch);
    setState({ project: state.project });
    flashSaved();
  } catch (e) {
    showError(e);
  }
}
