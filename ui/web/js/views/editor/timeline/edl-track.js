import { post, get } from "../../../api.js";
import { setState, state } from "../../../store.js";
import { toast } from "../../../components/toast.js";
import { deletedGaps } from "./edl-utils.js";
import { setSelection, clearSelection, getSelection } from "./selection.js";
import { showContextMenu } from "./context-menu.js";

export function mountEdlTrack(el, ctx) {
  el._zoom = ctx.zoom;
  el._onSeek = ctx.onSeek;
  el._flashSaved = ctx.flashSaved;
  el._getTool = ctx.getTool || (() => "select");
  el._actions = ctx.actions || {};
  renderEdl(el, ctx.edl);
  wireRangeSelect(el);
}

export function refreshEdlTrack(el, { edl, zoom }) {
  if (zoom != null) el._zoom = zoom;
  renderEdl(el, edl);
}

function renderEdl(el, edl) {
  el.innerHTML = "";
  const segs = edl?.segments;
  if (!segs?.length) return;
  const zoom = el._zoom;
  const prev = getSelection();

  segs.forEach((s, i) => {
    const block = document.createElement("div");
    block.className = "tl-seg";
    block.dataset.idx = String(i);
    block.style.left = `${s.output_start * zoom}px`;
    block.style.width = `${Math.max(2, (s.output_end - s.output_start) * zoom)}px`;
    block.title = `${fmtT(s.source_start)} – ${fmtT(s.source_end)}`;
    block.innerHTML = `<div class="tl-seg-thumbs" aria-hidden="true"></div><span class="tl-seg-lbl">${fmtT(s.output_start)}</span>`;
    block.addEventListener("click", (e) => onSegClick(e, block, s, i, el));
    block.addEventListener("dblclick", (e) => {
      e.stopPropagation();
      el._onSeek(s.output_start);
    });
    block.addEventListener("contextmenu", (e) => {
      e.preventDefault();
      e.stopPropagation();
      selectSeg(el, block, s, i);
      showContextMenu(e.clientX, e.clientY, [
        { label: "Split at playhead", action: () => el._actions.split?.() },
        { label: "Delete", action: () => el._actions.deleteSelection?.() },
        { label: "Trim start to playhead", action: () => el._actions.trimStart?.() },
        { label: "Trim end to playhead", action: () => el._actions.trimEnd?.() },
      ]);
    });
    wireTrimHandles(block, s, el);
    if (prev.kind === "seg" && prev.data?.idx === i) block.classList.add("selected");
    el.appendChild(block);
  });

  deletedGaps(segs).forEach((g, gi) => {
    const gap = document.createElement("div");
    gap.className = "tl-gap";
    gap.dataset.gi = String(gi);
    gap.style.left = `${g.output_at * zoom}px`;
    gap.style.width = `${Math.max(2, (g.source_end - g.source_start) * zoom)}px`;
    gap.title = "Deleted — click to select, Restore to bring back";
    gap.addEventListener("click", (e) => {
      e.stopPropagation();
      setSelection("gap", { ...g, el: gap, gi }, { edlEl: el });
      el._onSeek(g.output_at);
    });
    gap.addEventListener("dblclick", (e) => {
      e.stopPropagation();
      restoreGap(g, el._flashSaved);
    });
    gap.addEventListener("contextmenu", (e) => {
      e.preventDefault();
      e.stopPropagation();
      setSelection("gap", { ...g, el: gap, gi }, { edlEl: el });
      showContextMenu(e.clientX, e.clientY, [
        { label: "Restore", action: () => restoreGap(g, el._flashSaved) },
        { label: "Merge / Close gap", action: () => restoreGap(g, el._flashSaved) },
      ]);
    });
    if (prev.kind === "gap" && prev.data?.gi === gi) gap.classList.add("selected");
    el.appendChild(gap);
  });
}

function onSegClick(e, block, seg, idx, el) {
  e.stopPropagation();
  selectSeg(el, block, seg, idx);
  if (el._getTool() === "blade") {
    const canvas = el.closest(".tl-canvas");
    const r = canvas.getBoundingClientRect();
    const outTime = Math.max(0, (e.clientX - r.left) / el._zoom);
    el._onSeek(outTime);
    el._actions.split?.();
  }
}

function selectSeg(el, block, seg, idx) {
  setSelection("seg", { seg, idx, el: block }, { edlEl: el });
}

function wireTrimHandles(block, seg, trackEl) {
  [{ side: "left", cls: "left" }, { side: "right", cls: "right" }].forEach(({ side, cls }) => {
    const h = document.createElement("div");
    h.className = `tl-trim ${cls}`;
    block.appendChild(h);
    let startX = 0, origSrc = 0;
    h.addEventListener("pointerdown", (e) => {
      e.stopPropagation();
      h.setPointerCapture(e.pointerId);
      startX = e.clientX;
      origSrc = side === "left" ? seg.source_start : seg.source_end;
    });
    h.addEventListener("pointermove", (e) => {
      if (!h.hasPointerCapture?.(e.pointerId) && e.buttons === 0) return;
      const dx = e.clientX - startX;
      const dt = dx / trackEl._zoom;
      const newSrc = origSrc + dt;
      if (side === "left") {
        block.style.left = `${(seg.output_start + dt) * trackEl._zoom}px`;
        block.style.width = `${Math.max(2, (seg.output_end - seg.output_start - dt) * trackEl._zoom)}px`;
        h._pending = {
          start: Math.min(newSrc, origSrc),
          end: Math.max(newSrc, origSrc),
          deleted: newSrc > origSrc,
        };
      } else {
        block.style.width = `${Math.max(2, (seg.output_end - seg.output_start + dt) * trackEl._zoom)}px`;
        h._pending = {
          start: Math.min(origSrc, newSrc),
          end: Math.max(origSrc, newSrc),
          deleted: newSrc < origSrc,
        };
      }
    });
    h.addEventListener("pointerup", async () => {
      if (!h._pending) return;
      const p = h._pending;
      h._pending = null;
      try {
        await post("/words/range", { start_s: p.start, end_s: p.end, deleted: p.deleted });
        const fresh = await get("/edl");
        setState({ edl: fresh });
        refreshEdlTrack(trackEl, { edl: fresh });
        trackEl._flashSaved();
      } catch (err) {
        toast(String(err.message || err), "danger");
      }
    });
  });
}

function wireRangeSelect(el) {
  let dragging = false;
  let startX = 0;
  let band = null;

  el.addEventListener("pointerdown", (e) => {
    if (el._getTool() !== "select") return;
    if (e.target.closest(".tl-seg, .tl-gap, .tl-trim")) return;
    dragging = true;
    startX = e.clientX;
    const r = el.getBoundingClientRect();
    const left = e.clientX - r.left + el.parentElement.scrollLeft;
    band = document.createElement("div");
    band.className = "tl-range";
    band.style.left = `${left}px`;
    band.style.width = "0px";
    el.appendChild(band);
    el.setPointerCapture?.(e.pointerId);
  });

  el.addEventListener("pointermove", (e) => {
    if (!dragging || !band) return;
    const scroll = el.parentElement?.scrollLeft || 0;
    const r = el.getBoundingClientRect();
    const x0 = startX - r.left + scroll;
    const x1 = e.clientX - r.left + scroll;
    const left = Math.min(x0, x1);
    const width = Math.abs(x1 - x0);
    band.style.left = `${left}px`;
    band.style.width = `${width}px`;
  });

  el.addEventListener("pointerup", (e) => {
    if (!dragging || !band) return;
    dragging = false;
    const scroll = el.parentElement?.scrollLeft || 0;
    const r = el.getBoundingClientRect();
    const x0 = startX - r.left + scroll;
    const x1 = e.clientX - r.left + scroll;
    const t0 = Math.min(x0, x1) / el._zoom;
    const t1 = Math.max(x0, x1) / el._zoom;
    if (t1 - t0 < 0.05) {
      band.remove();
      clearSelection({ edlEl: el });
      return;
    }
    setSelection("range", { outStart: t0, outEnd: t1, el: band }, { edlEl: el });
  });
}

export async function restoreGap(gap, flashSaved) {
  try {
    await post("/words/range", {
      start_s: gap.source_start,
      end_s: gap.source_end,
      deleted: false,
    });
    const fresh = await get("/edl");
    setState({ edl: fresh });
    flashSaved();
    clearSelection();
  } catch (err) {
    toast(String(err.message || err), "danger");
  }
}

export async function deleteSegRange(seg, flashSaved) {
  try {
    await post("/words/range", {
      start_s: seg.source_start,
      end_s: seg.source_end,
      deleted: true,
    });
    const fresh = await get("/edl");
    setState({ edl: fresh });
    flashSaved();
    clearSelection();
  } catch (err) {
    toast(String(err.message || err), "danger");
  }
}

export async function deleteOutputRange(outStart, outEnd, flashSaved) {
  const segs = state.edl?.segments || [];
  const hits = segs.filter((s) => s.output_end > outStart && s.output_start < outEnd);
  if (!hits.length) return;
  const srcStart = Math.min(...hits.map((s) => {
    const o0 = Math.max(outStart, s.output_start);
    return s.source_start + (o0 - s.output_start);
  }));
  const srcEnd = Math.max(...hits.map((s) => {
    const o1 = Math.min(outEnd, s.output_end);
    return s.source_start + (o1 - s.output_start);
  }));
  try {
    await post("/words/range", { start_s: srcStart, end_s: srcEnd, deleted: true });
    const fresh = await get("/edl");
    setState({ edl: fresh });
    flashSaved();
    clearSelection();
  } catch (err) {
    toast(String(err.message || err), "danger");
  }
}

export async function trimSegToPlayhead(side, flashSaved) {
  const sel = getSelection();
  if (sel.kind !== "seg" || !sel.data?.seg) return;
  const seg = sel.data.seg;
  const src = state.playheadSrc;
  if (src == null || src < seg.source_start || src > seg.source_end) {
    toast("Playhead must be inside the selected segment", "danger");
    return;
  }
  const range = side === "start"
    ? { start_s: seg.source_start, end_s: src, deleted: true }
    : { start_s: src, end_s: seg.source_end, deleted: true };
  if (range.end_s - range.start_s < 0.02) return;
  try {
    await post("/words/range", range);
    const fresh = await get("/edl");
    setState({ edl: fresh });
    flashSaved();
    clearSelection();
  } catch (err) {
    toast(String(err.message || err), "danger");
  }
}

const fmtT = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
