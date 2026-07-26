import { get, post } from "../../../api.js";
import { state, setState, subscribe } from "../../../store.js";
import { toast } from "../../../components/toast.js";
import { mountRuler, updateRuler } from "./ruler.js";
import { mountPlayhead, updatePlayhead, setPlayheadZoom } from "./playhead.js";
import { mountEdlTrack, refreshEdlTrack } from "./edl-track.js";
import { mountBrollTrack, refreshBrollTrack } from "./broll-track.js";
import { mountMarkers, refreshMarkers } from "./markers.js";
import { wireToolbar } from "./toolbar.js";
import { outToSrc, edlDuration, deletedGaps } from "./edl-utils.js";

const DEFAULT_ZOOM = 80;

export async function mountTimeline(el, { copy, flashSaved, getVideo, onSeekOutput }) {
  let zoom = DEFAULT_ZOOM;
  let edl = null;

  try { edl = await get("/edl"); setState({ edl }); } catch { /* no edl yet */ }

  let duration = edlDuration(edl) || state.project?.sources?.[0]?.duration || 60;

  el.innerHTML = buildShell(copy);
  const canvas = el.querySelector(".tl-canvas");
  const scroll = el.querySelector(".tl-scroll");
  const phLayer = el.querySelector(".tl-playhead-layer");
  const edlEl = el.querySelector(".tl-edl-track");
  const brollEl = el.querySelector(".tl-broll-track");
  const markersEl = el.querySelector(".tl-markers-track");

  canvas.style.minWidth = `${duration * zoom}px`;

  mountRuler(el.querySelector(".tl-ruler"), { duration, zoom });
  mountPlayhead(phLayer, { zoom, scrollEl: scroll, onSeek: onSeekOutput, getDuration: () => duration });
  mountEdlTrack(edlEl, { edl, zoom, flashSaved, onSeek: onSeekOutput });
  mountBrollTrack(brollEl, { zoom, flashSaved });
  mountMarkers(markersEl, { zoom, flashSaved });

  canvas.addEventListener("click", (e) => {
    if (e.target.closest(".tl-seg, .tl-gap, .tl-clip, .tl-marker, .tl-playhead-line, .tl-trim")) return;
    const r = canvas.getBoundingClientRect();
    onSeekOutput(Math.max(0, (e.clientX - r.left) / zoom));
  });

  const blade = async () => {
    const srcTime = state.playheadSrc ?? 0;
    try {
      await post("/words/range", { start: srcTime, end: srcTime, deleted: true });
      const fresh = await get("/edl");
      setState({ edl: fresh });
      toast(copy.bladed, "ok");
      flashSaved();
    } catch (err) { toast(String(err.message || err), "danger"); }
  };

  const restore = async () => {
    const srcTime = state.playheadSrc ?? 0;
    const gaps = deletedGaps(edl?.segments || []);
    const g = gaps.find((gap) => srcTime >= gap.source_start && srcTime <= gap.source_end);
    if (!g) return;
    try {
      await post("/words/range", { start: g.source_start, end: g.source_end, deleted: false });
      const fresh = await get("/edl");
      setState({ edl: fresh });
      toast(copy.restored, "ok");
      flashSaved();
    } catch (err) { toast(String(err.message || err), "danger"); }
  };

  const handleUndo = async () => {
    try { await post("/project/undo", {}); const p = await get("/project"); setState({ project: p }); const e = await get("/edl").catch(() => null); if (e) setState({ edl: e }); flashSaved(); } catch (err) { toast(String(err.message || err), "danger"); }
  };

  const handleRedo = async () => {
    try { await post("/project/redo", {}); const p = await get("/project"); setState({ project: p }); const e = await get("/edl").catch(() => null); if (e) setState({ edl: e }); flashSaved(); } catch (err) { toast(String(err.message || err), "danger"); }
  };

  wireToolbar(el.querySelector(".tl-toolbar"), {
    copy, brollEl, markersEl, flashSaved, onUndo: handleUndo, onRedo: handleRedo,
    onZoom: (dir) => { zoom = Math.max(20, Math.min(400, zoom * (dir > 0 ? 1.4 : 0.7))); repaint(); },
    blade, restore,
  });

  el._blade = blade;
  el._undo = handleUndo;
  el._redo = handleRedo;

  function repaint() {
    canvas.style.minWidth = `${duration * zoom}px`;
    updateRuler(el.querySelector(".tl-ruler"), zoom, duration);
    setPlayheadZoom(phLayer, zoom);
    updatePlayhead(phLayer, state.playheadOut || 0);
    refreshEdlTrack(edlEl, { edl, zoom });
    refreshBrollTrack(brollEl, zoom);
    refreshMarkers(markersEl, zoom);
  }

  const unsub = subscribe((st) => {
    if (st.edl && st.edl !== edl) {
      edl = st.edl;
      const d = edlDuration(edl);
      if (d) duration = d;
      repaint();
    }
    updatePlayhead(phLayer, st.playheadOut || 0);
    if (st.project) refreshBrollTrack(brollEl, null);
  });
  el._unsub = unsub;
}

function buildShell(copy) {
  return `<div class="tl-wrap">
    <div class="tl-toolbar">
      <button class="tl-btn" data-a="blade" title="Blade (B)">✂ ${copy.blade}</button>
      <button class="tl-btn ghost" data-a="restore" title="Restore gap">↩ ${copy.restore}</button>
      <span class="tl-sep"></span>
      <button class="tl-btn ghost" data-a="import">+ ${copy.import}</button>
      <button class="tl-btn ghost" data-a="distribute">⇄ ${copy.distribute}</button>
      <button class="tl-btn ghost" data-a="cleanup">✦ ${copy.cleanup}</button>
      <button class="tl-btn ghost" data-a="marker">◆ ${copy.addMarker}</button>
      <span class="tl-sep"></span>
      <button class="tl-btn ghost" data-a="undo" title="Undo (⌘Z)">↩ ${copy.undo}</button>
      <button class="tl-btn ghost" data-a="redo" title="Redo (⌘⇧Z)">↪ ${copy.redo}</button>
      <span class="tl-spacer"></span>
      <button class="tl-btn ghost" data-a="zoom-out" title="Zoom out (−)">${copy.zoomOut}</button>
      <button class="tl-btn ghost" data-a="zoom-in" title="Zoom in (+)">${copy.zoomIn}</button>
    </div>
    <div class="tl-body">
      <div class="tl-gutter">
        <div class="tl-gutter-ruler"></div>
        <div class="tl-gutter-label h-aroll">${copy.aroll}</div>
        <div class="tl-gutter-label h-broll">${copy.broll}</div>
        <div class="tl-gutter-label h-markers">${copy.markers}</div>
      </div>
      <div class="tl-scroll">
        <div class="tl-canvas">
          <div class="tl-ruler"></div>
          <div class="tl-edl-track"></div>
          <div class="tl-broll-track"></div>
          <div class="tl-markers-track"></div>
          <div class="tl-playhead-layer"></div>
        </div>
      </div>
    </div>
  </div>`;
}
