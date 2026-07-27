import { post } from "../../api.js";
import { state, setState, subscribe } from "../../store.js";
import { toast } from "../../components/toast.js";
import { paintCaption } from "./caption_preview.js";
import { srcToOut, nextKeptSeg } from "./timeline/edl-utils.js";

export function mountStage(el, { copy, flashSaved }) {
  const project = state.project;
  const zones = state.safezones || {};
  el.innerHTML = `<div class="stage-frame">
    <div class="stage-well settle">
      <div class="stage">
        <video class="stage-video" playsinline loop preload="metadata"
          src="/media/source?v=${encodeURIComponent(state.projectPath || "")}"></video>
        <audio class="stage-music" preload="none" loop></audio>
        <div class="safe" hidden></div>
        <div class="stage-crop" hidden>
          <div class="stage-crop-window" title="Drag to pan framing"></div>
        </div>
        <div class="inset"><span class="inset-handle" title="Drag to resize"></span></div>
        <div class="caption"></div>
      </div>
    </div>
    </div>
    <div class="transport">
      <button type="button" class="play-toggle" aria-label="${copy.play}">
        <span class="icon-play" aria-hidden="true"></span>
      </button>
      <input type="range" class="scrub" min="0" max="1000" value="0" step="1" aria-label="Seek" />
      <span class="mono timecode">0:00</span>
    </div>
    <div class="stage-controls">
      <label><input type="checkbox" class="sz-toggle" /> ${copy.safezones}</label>
      <select class="sz-platform">
        ${Object.keys(zones).map((k) => `<option value="${k}">${k}</option>`).join("")}
      </select>
      <label><input type="checkbox" class="crop-toggle" /> ${copy.cropFrame || "Crop"}</label>
    </div>`;

  const stage = el.querySelector(".stage");
  const inset = el.querySelector(".inset");
  const handle = el.querySelector(".inset-handle");
  const caption = el.querySelector(".caption");
  const safe = el.querySelector(".safe");
  const video = el.querySelector(".stage-video");
  const crop = el.querySelector(".stage-crop");
  el._video = video;

  video.addEventListener("error", () => {
    toast("Could not load video preview — check the source file path", "danger");
  });
  const musicEl = el.querySelector(".stage-music");
  el._music = musicEl;
  wireTransport(el, video, musicEl, copy);
  wirePlayheadSync(el, video, musicEl);
  syncStageMusic(musicEl);

  function applyLayout() {
    const p = state.project;
    inset.style.left = `${p.layers.inset.x * 100}%`;
    inset.style.top = `${p.layers.inset.y * 100}%`;
    inset.style.width = `${p.layers.inset.w * 100}%`;
    const px = (p.layers.pan_x ?? 0.5) * 100;
    const py = (p.layers.pan_y ?? 0.5) * 100;
    video.style.objectPosition = `${px}% ${py}%`;
    paintCaption(caption, p, state.presets || {});
  }
  applyLayout();
  el._refreshStage = applyLayout;

  wireSafezones(el, safe, zones);
  wireInsetMove(stage, inset, flashSaved);
  wireInsetResize(stage, inset, handle, flashSaved);
  wireCaptionDrag(stage, caption, flashSaved);
  wireCropMode(el, crop, video, flashSaved, applyLayout);

  el.querySelector(".stage-well").addEventListener(
    "animationend",
    (e) => e.currentTarget.classList.remove("settle"),
    { once: true },
  );
}

function wireTransport(el, video, musicEl, copy) {
  const btn = el.querySelector(".play-toggle");
  const scrub = el.querySelector(".scrub");
  const time = el.querySelector(".timecode");
  const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
  const paintState = () => {
    btn.classList.toggle("playing", !video.paused);
    btn.setAttribute("aria-label", video.paused ? copy.play : copy.pause);
  };
  btn.onclick = () => {
    if (video.paused) {
      syncStageMusic(musicEl);
      video.muted = false;
      video.play().catch(() => {});
      if (musicEl?.src) musicEl.play().catch(() => {});
    } else {
      video.pause();
      musicEl?.pause();
    }
  };
  video.addEventListener("play", () => {
    paintState();
    if (musicEl?.src && musicEl.paused) musicEl.play().catch(() => {});
  });
  video.addEventListener("pause", () => {
    paintState();
    musicEl?.pause();
  });

  let jumping = false;
  video.addEventListener("timeupdate", () => {
    if (video.duration) scrub.value = String((video.currentTime / video.duration) * 1000);
    time.textContent = `${fmt(video.currentTime)} / ${fmt(video.duration || 0)}`;

    // Skip-deleted playback: jump over deleted source regions
    const segs = state.edl?.segments;
    if (segs?.length && !video.paused && !jumping) {
      const inKeep = segs.some((s) => video.currentTime >= s.source_start && video.currentTime <= s.source_end + 0.01);
      if (!inKeep) {
        const next = nextKeptSeg(video.currentTime, segs);
        jumping = true;
        if (next) video.currentTime = next.source_start;
        else video.pause();
        setTimeout(() => { jumping = false; }, 80);
      }
    }

    // Broadcast output time to store for timeline playhead
    const outTime = segs?.length ? (srcToOut(video.currentTime, segs) ?? state.playheadOut) : video.currentTime;
    setState({ playheadSrc: video.currentTime, playheadOut: outTime ?? 0 });
    syncMusicClock(musicEl, outTime ?? video.currentTime);
  });

  scrub.oninput = () => {
    if (video.duration) video.currentTime = (Number(scrub.value) / 1000) * video.duration;
  };
}

function wirePlayheadSync(el, video, musicEl) {
  if (el._phUnsub) el._phUnsub();
  el._phUnsub = subscribe((st) => {
    // Sync video when timeline seeks externally (threshold avoids feedback loop)
    if (st.playheadSrc != null && Math.abs(st.playheadSrc - video.currentTime) > 0.15) {
      video.currentTime = st.playheadSrc;
    }
    if (st.project !== el._musicProjectRef) {
      el._musicProjectRef = st.project;
      syncStageMusic(musicEl);
    }
  });
}

function syncStageMusic(musicEl) {
  if (!musicEl) return;
  const audio = state.project?.audio || {};
  const id = audio.music_track_id;
  const gainDb = Number(audio.music_gain_db ?? -18);
  musicEl.volume = Math.min(1, Math.max(0, 10 ** (gainDb / 20)));
  if (!id) {
    musicEl.pause();
    musicEl.removeAttribute("src");
    return;
  }
  const next = `/media/source?id=${encodeURIComponent(id)}`;
  if (musicEl.dataset.trackId !== id) {
    const wasPlaying = !musicEl.paused && musicEl.src;
    musicEl.dataset.trackId = id;
    musicEl.src = next;
    if (wasPlaying) musicEl.play().catch(() => {});
  }
}

function syncMusicClock(musicEl, outTime) {
  if (!musicEl?.src || !musicEl.duration || Number.isNaN(musicEl.duration)) return;
  const target = outTime % musicEl.duration;
  if (Math.abs(musicEl.currentTime - target) > 0.35) {
    musicEl.currentTime = target;
  }
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

function wireCropMode(el, crop, video, flashSaved, applyLayout) {
  const toggle = el.querySelector(".crop-toggle");
  const win = crop.querySelector(".stage-crop-window");
  toggle.onchange = () => {
    crop.hidden = !toggle.checked;
    el.querySelector(".stage-well").classList.toggle("cropping", toggle.checked);
  };
  let startX = 0, startY = 0, ox = 0.5, oy = 0.5;
  win.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    win.setPointerCapture(e.pointerId);
    startX = e.clientX;
    startY = e.clientY;
    ox = state.project.layers.pan_x ?? 0.5;
    oy = state.project.layers.pan_y ?? 0.5;
  });
  win.addEventListener("pointermove", (e) => {
    if (!win.hasPointerCapture(e.pointerId)) return;
    const r = el.querySelector(".stage").getBoundingClientRect();
    const dx = (e.clientX - startX) / r.width;
    const dy = (e.clientY - startY) / r.height;
    const pan_x = clamp01(ox - dx);
    const pan_y = clamp01(oy - dy);
    state.project.layers.pan_x = pan_x;
    state.project.layers.pan_y = pan_y;
    video.style.objectPosition = `${pan_x * 100}% ${pan_y * 100}%`;
  });
  win.addEventListener("pointerup", async () => {
    try {
      await post("/layers", {
        pan_x: state.project.layers.pan_x ?? 0.5,
        pan_y: state.project.layers.pan_y ?? 0.5,
      });
      setState({ project: state.project });
      flashSaved();
      applyLayout();
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
