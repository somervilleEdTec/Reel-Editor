import { post } from "../../api.js";
import { setState, state } from "../../store.js";
import { openMusicLibrary } from "../../components/music_library.js";
import { showError, sourceLabel } from "./inspector_helpers.js";

export function mountInspectorAudio(el, { copy, flashSaved }) {
  const audio = state.project.audio || {};
  el.innerHTML = `<div class="cluster">
    <p class="section-label">${copy.audio}</p>
    <div class="music-source-row">
      <label class="field grow">${copy.musicSource}<select class="music-source"></select></label>
      <button type="button" class="secondary browse-music">${copy.browseMusic || "Browse free music"}</button>
    </div>
    <label class="field">${copy.musicGain}
      <input type="number" class="music-gain" step="0.5" value="${audio.music_gain_db ?? -18}" />
    </label>
    <label class="field inline-check">
      <input type="checkbox" class="duck" ${audio.duck_under_speech ? "checked" : ""} /> ${copy.duckUnderSpeech}
    </label>
  </div>`;

  paintMusicSelect(el, copy);
  el.querySelector(".music-source").onchange = () =>
    saveAudio({ music_track_id: el.querySelector(".music-source").value || null }, flashSaved);
  el.querySelector(".music-gain").onchange = (e) => {
    saveAudio({ music_gain_db: Number(e.target.value) }, flashSaved);
  };
  el.querySelector(".duck").onchange = (e) => {
    saveAudio({ duck_under_speech: e.target.checked }, flashSaved);
  };
  el.querySelector(".browse-music").onclick = () => {
    openMusicLibrary({
      copy,
      onUsed: (result) => {
        state.project.sources = result.sources;
        state.project.audio = result.audio;
        setState({ project: state.project });
        paintMusicSelect(el, copy);
        flashSaved();
      },
    });
  };
}

function paintMusicSelect(el, copy) {
  const select = el.querySelector(".music-source");
  const audio = state.project.audio || {};
  const current = audio.music_track_id || "";
  select.innerHTML = "";
  select.appendChild(new Option(copy.noMusicSource, ""));
  const sources = state.project.sources || [];
  const preferred = sources.filter((s) => s.role === "music" || s.has_audio);
  const rest = sources.filter((s) => !preferred.includes(s));
  for (const src of [...preferred, ...rest]) {
    select.appendChild(new Option(sourceLabel(src), src.id));
  }
  select.value = current;
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
