import { get, post } from "../../../api.js";
import { state, setState, subscribe } from "../../../store.js";
import { toast } from "../../../components/toast.js";
import { mountRuler, updateRuler } from "./ruler.js";
import { mountPlayhead, updatePlayhead, setPlayheadZoom } from "./playhead.js";
import {
  mountEdlTrack, refreshEdlTrack, restoreGap, deleteSegRange,
  deleteOutputRange, trimSegToPlayhead,
} from "./edl-track.js";
import { mountBrollTrack, refreshBrollTrack, deleteSelectedClip } from "./broll-track.js";
import { mountMarkers, refreshMarkers } from "./markers.js";
import { wireToolbar } from "./toolbar.js";
import { edlDuration, deletedGaps } from "./edl-utils.js";
import { getSelection, clearSelection } from "./selection.js";

const DEFAULT_ZOOM = 80;
const TL_H_KEY = "reelwrite.timelineHeight";

export async function mountTimeline(el, { copy, flashSaved, getVideo, onSeekOutput }) {
  let zoom = DEFAULT_ZOOM;
  let edl = null;
  let tool = "select";

  try { edl = await get("/edl"); setState({ edl }); } catch { /* no edl yet */ }

  let duration = edlDuration(edl) || state.project?.sources?.[0]?.duration || 60;

  el.innerHTML = `<div class="tl-resize" title="Drag to resize timeline"></div>${buildShell(copy)}`;
  wireResize(el);

  const canvas = el.querySelector(".tl-canvas");
  const scroll = el.querySelector(".tl-scroll");
  const phLayer = el.querySelector(".tl-playhead-layer");
  const edlEl = el.querySelector(".tl-edl-track");
  const brollEl = el.querySelector(".tl-broll-track");
  const markersEl = el.querySelector(".tl-markers-track");

  canvas.style.minWidth = `${duration * zoom}px`;

  const blade = async () => {
    const srcTime = state.playheadSrc ?? 0;
    try {
      await post("/words/range", {
        start_s: Math.max(0, srcTime - 0.04),
        end_s: srcTime + 0.04,
        deleted: true,
      });
      const fresh = await get("/edl");
      setState({ edl: fresh });
      toast(copy.bladed, "ok");
      flashSaved();
    } catch (err) { toast(String(err.message || err), "danger"); }
  };

  const restore = async () => {
    const sel = getSelection();
    if (sel.kind === "gap" && sel.data) {
      await restoreGap(sel.data, flashSaved);
      toast(copy.restored, "ok");
      return;
    }
    const srcTime = state.playheadSrc ?? 0;
    const gaps = deletedGaps(edl?.segments || []);
    const g = gaps.find((gap) => srcTime >= gap.source_start && srcTime <= gap.source_end);
    if (!g) {
      toast(copy.restoreHint || "Select a deleted gap first", "danger");
      return;
    }
    await restoreGap(g, flashSaved);
    toast(copy.restored, "ok");
  };

  const merge = async () => {
    const sel = getSelection();
    if (sel.kind === "gap" && sel.data) {
      await restoreGap(sel.data, flashSaved);
      toast(copy.merged || copy.restored, "ok");
      return;
    }
    const srcTime = state.playheadSrc ?? 0;
    const gaps = deletedGaps(edl?.segments || []);
    const g = gaps.find((gap) => srcTime >= gap.source_start - 0.05 && srcTime <= gap.source_end + 0.05);
    if (!g) {
      toast(copy.mergeHint || "Select a gap between segments to merge", "danger");
      return;
    }
    await restoreGap(g, flashSaved);
    toast(copy.merged || copy.restored, "ok");
  };

  const deleteSelection = async () => {
    const sel = getSelection();
    if (sel.kind === "clip") {
      await deleteSelectedClip(brollEl, flashSaved);
      toast(copy.deleteClip, "ok");
      return;
    }
    if (sel.kind === "seg" && sel.data?.seg) {
      await deleteSegRange(sel.data.seg, flashSaved);
      toast(copy.deletedSeg || "Segment removed", "ok");
      return;
    }
    if (sel.kind === "range" && sel.data) {
      await deleteOutputRange(sel.data.outStart, sel.data.outEnd, flashSaved);
      toast(copy.deletedSeg || "Range removed", "ok");
      return;
    }
    await deleteSelectedClip(brollEl, flashSaved);
  };

  const trimStart = () => trimSegToPlayhead("start", flashSaved);
  const trimEnd = () => trimSegToPlayhead("end", flashSaved);

  const actions = {
    split: blade,
    deleteSelection,
    restore,
    merge,
    trimStart,
    trimEnd,
  };

  mountRuler(el.querySelector(".tl-ruler"), { duration, zoom });
  mountPlayhead(phLayer, { zoom, scrollEl: scroll, onSeek: onSeekOutput, getDuration: () => duration });
  mountEdlTrack(edlEl, {
    edl, zoom, flashSaved, onSeek: onSeekOutput,
    getTool: () => tool, actions,
  });
  mountBrollTrack(brollEl, { zoom, flashSaved, actions });
  mountMarkers(markersEl, { zoom, flashSaved });

  canvas.addEventListener("click", (e) => {
    if (e.target.closest(".tl-seg, .tl-gap, .tl-clip, .tl-marker, .tl-playhead-line, .tl-trim, .tl-range")) return;
    const r = canvas.getBoundingClientRect();
    onSeekOutput(Math.max(0, (e.clientX - r.left) / zoom));
    clearSelection({ edlEl, brollEl, canvas });
  });

  scroll.addEventListener("wheel", (e) => {
    if (!(e.ctrlKey || e.metaKey)) return;
    e.preventDefault();
    zoom = Math.max(20, Math.min(400, zoom * (e.deltaY < 0 ? 1.15 : 0.87)));
    repaint();
  }, { passive: false });

  const handleUndo = async () => {
    try {
      await post("/project/undo", {});
      const p = await get("/project");
      setState({ project: p });
      const e = await get("/edl").catch(() => null);
      if (e) setState({ edl: e });
      flashSaved();
    } catch (err) { toast(String(err.message || err), "danger"); }
  };

  const handleRedo = async () => {
    try {
      await post("/project/redo", {});
      const p = await get("/project");
      setState({ project: p });
      const e = await get("/edl").catch(() => null);
      if (e) setState({ edl: e });
      flashSaved();
    } catch (err) { toast(String(err.message || err), "danger"); }
  };

  const fitZoom = () => {
    const w = scroll.clientWidth || 600;
    zoom = Math.max(20, Math.min(400, (w - 8) / Math.max(duration, 1)));
    repaint();
  };

  wireToolbar(el.querySelector(".tl-toolbar"), {
    copy, brollEl, markersEl, flashSaved,
    onUndo: handleUndo, onRedo: handleRedo,
    onZoom: (dir) => { zoom = Math.max(20, Math.min(400, zoom * (dir > 0 ? 1.4 : 0.7))); repaint(); },
    onFit: fitZoom,
    setTool: (t) => { tool = t; canvas.classList.toggle("blade-mode", t === "blade"); },
    getTool: () => tool,
    split: blade,
    restore, merge, deleteSelection,
    trimStart, trimEnd,
  });

  el._blade = blade;
  el._undo = handleUndo;
  el._redo = handleRedo;
  el._deleteSelected = deleteSelection;
  el._setTool = (t) => {
    tool = t;
    canvas.classList.toggle("blade-mode", t === "blade");
    el.querySelector("[data-tool=select]")?.classList.toggle("active", t === "select");
    el.querySelector("[data-tool=blade]")?.classList.toggle("active", t === "blade");
  };
  el._getTool = () => tool;
  el._trimStart = trimStart;
  el._trimEnd = trimEnd;
  el._fitZoom = fitZoom;
  el._merge = merge;
  el._restore = restore;

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

function wireResize(el) {
  const handle = el.querySelector(".tl-resize");
  const saved = Number(localStorage.getItem(TL_H_KEY));
  if (saved >= 140 && saved <= 420) el.style.setProperty("--tl-h", `${saved}px`);

  let startY = 0;
  let startH = 0;
  handle.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    handle.classList.add("dragging");
    startY = e.clientY;
    startH = el.getBoundingClientRect().height;
    handle.setPointerCapture(e.pointerId);
  });
  handle.addEventListener("pointermove", (e) => {
    if (!handle.hasPointerCapture(e.pointerId)) return;
    const dy = startY - e.clientY;
    const next = Math.max(140, Math.min(420, startH + dy));
    el.style.setProperty("--tl-h", `${next}px`);
  });
  handle.addEventListener("pointerup", () => {
    handle.classList.remove("dragging");
    const h = el.getBoundingClientRect().height;
    localStorage.setItem(TL_H_KEY, String(Math.round(h)));
  });
}

function buildShell(copy) {
  return `<div class="tl-wrap">
    <div class="tl-toolbar">
      <span class="tl-group">
        <button class="tl-btn ghost active" data-tool="select" title="${copy.selectTip || "Select (V)"}">${copy.select || "Select"}</button>
        <button class="tl-btn ghost" data-tool="blade" title="${copy.bladeTip || "Blade (B)"}">✂ ${copy.blade}</button>
      </span>
      <span class="tl-sep"></span>
      <span class="tl-group">
        <button class="tl-btn" data-a="split" title="${copy.splitTip || "Split at playhead"}">${copy.split || "Split"}</button>
        <button class="tl-btn ghost" data-a="delete" title="${copy.deleteTip || "Delete selection"}">${copy.delete || "Delete"}</button>
        <button class="tl-btn ghost" data-a="restore" title="${copy.restoreTip || "Restore gap"}">↩ ${copy.restore}</button>
        <button class="tl-btn ghost" data-a="merge" title="${copy.mergeTip || "Merge / close gap"}">${copy.merge || "Merge"}</button>
        <button class="tl-btn ghost" data-a="trim-start" title="${copy.trimStartTip || "Trim start to playhead ("}">[</button>
        <button class="tl-btn ghost" data-a="trim-end" title="${copy.trimEndTip || "Trim end to playhead )"}">]</button>
      </span>
      <span class="tl-sep"></span>
      <span class="tl-group">
        <button class="tl-btn ghost" data-a="import">+ ${copy.import}</button>
        <button class="tl-btn ghost" data-a="distribute">⇄ ${copy.distribute}</button>
        <button class="tl-btn ghost" data-a="more" title="More">⋯</button>
      </span>
      <span class="tl-group tl-more" hidden>
        <button class="tl-btn ghost" data-a="cleanup">✦ ${copy.cleanup}</button>
        <button class="tl-btn ghost" data-a="marker">◆ ${copy.addMarker}</button>
      </span>
      <span class="tl-sep"></span>
      <button class="tl-btn ghost" data-a="undo" title="Undo (⌘Z)">↩ ${copy.undo}</button>
      <button class="tl-btn ghost" data-a="redo" title="Redo (⌘⇧Z)">↪ ${copy.redo}</button>
      <span class="tl-spacer"></span>
      <button class="tl-btn ghost" data-a="zoom-out" title="Zoom out (−)">${copy.zoomOut}</button>
      <button class="tl-btn ghost" data-a="fit" title="${copy.fitTip || "Fit timeline"}">${copy.fit || "Fit"}</button>
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
