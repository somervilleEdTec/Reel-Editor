import { post, get } from "../../../api.js";
import { setState } from "../../../store.js";
import { toast } from "../../../components/toast.js";
import { deletedGaps } from "./edl-utils.js";

export function mountEdlTrack(el, { edl, zoom, flashSaved, onSeek }) {
  el._zoom = zoom;
  el._onSeek = onSeek;
  el._flashSaved = flashSaved;
  renderEdl(el, edl);
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

  segs.forEach((s, i) => {
    const block = document.createElement("div");
    block.className = "tl-seg";
    block.style.left = `${s.output_start * zoom}px`;
    block.style.width = `${Math.max(2, (s.output_end - s.output_start) * zoom)}px`;
    block.title = `${fmtT(s.source_start)} – ${fmtT(s.source_end)}`;
    block.innerHTML = `<span class="tl-seg-lbl">${fmtT(s.output_start)}</span>`;
    block.addEventListener("click", (e) => { e.stopPropagation(); el._onSeek(s.output_start); });
    wireTrimHandles(block, s, i, el, edl);
    el.appendChild(block);
  });

  deletedGaps(segs).forEach((g) => {
    const gap = document.createElement("div");
    gap.className = "tl-gap";
    gap.style.left = `${g.output_at * zoom}px`;
    gap.style.width = `${Math.max(2, (g.source_end - g.source_start) * zoom)}px`;
    gap.title = "Deleted — click to restore";
    gap.addEventListener("click", (e) => { e.stopPropagation(); restoreGap(g, el._flashSaved); });
    el.appendChild(gap);
  });
}

function wireTrimHandles(block, seg, _idx, trackEl, edl) {
  [{ side: "left", cls: "left" }, { side: "right", cls: "right" }].forEach(({ side, cls }) => {
    const h = document.createElement("div");
    h.className = `tl-trim ${cls}`;
    block.appendChild(h);
    let startX = 0, origSrc = 0;
    h.addEventListener("pointerdown", (e) => {
      e.stopPropagation(); h.setPointerCapture(e.pointerId);
      startX = e.clientX;
      origSrc = side === "left" ? seg.source_start : seg.source_end;
    });
    h.addEventListener("pointermove", (e) => {
      const dx = e.clientX - startX;
      const dt = dx / trackEl._zoom;
      const newSrc = origSrc + dt;
      if (side === "left") {
        const del = { start: newSrc < origSrc ? newSrc : origSrc, end: newSrc < origSrc ? origSrc : newSrc, deleted: newSrc > origSrc };
        block.style.left = `${(seg.output_start + dt) * trackEl._zoom}px`;
        block.style.width = `${Math.max(2, (seg.output_end - seg.output_start - dt) * trackEl._zoom)}px`;
        h._pending = del;
      } else {
        block.style.width = `${Math.max(2, (seg.output_end - seg.output_start + dt) * trackEl._zoom)}px`;
        h._pending = { start: Math.min(origSrc, newSrc), end: Math.max(origSrc, newSrc), deleted: newSrc < origSrc };
      }
    });
    h.addEventListener("pointerup", async () => {
      if (!h._pending) return;
      const p = h._pending; h._pending = null;
      try {
        await post("/words/range", {
          start_s: p.start,
          end_s: p.end,
          deleted: p.deleted,
        });
        const fresh = await get("/edl");
        setState({ edl: fresh }); refreshEdlTrack(trackEl, { edl: fresh });
        trackEl._flashSaved();
      } catch (err) { toast(String(err.message || err), "danger"); }
    });
  });
}

async function restoreGap(gap, flashSaved) {
  try {
    await post("/words/range", {
      start_s: gap.source_start,
      end_s: gap.source_end,
      deleted: false,
    });
    const fresh = await get("/edl");
    setState({ edl: fresh });
    flashSaved();
  } catch (err) { toast(String(err.message || err), "danger"); }
}

const fmtT = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
