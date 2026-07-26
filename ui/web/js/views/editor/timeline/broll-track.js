import { post } from "../../../api.js";
import { state, setState } from "../../../store.js";
import { toast } from "../../../components/toast.js";
import { openFileBrowser } from "../../../components/filebrowser.js";

export function mountBrollTrack(el, { zoom, flashSaved }) {
  el._zoom = zoom;
  el._flashSaved = flashSaved;
  renderBroll(el);
}

export function refreshBrollTrack(el, zoom) {
  if (zoom != null) el._zoom = zoom;
  renderBroll(el);
}

function renderBroll(el) {
  el.innerHTML = "";
  const clips = state.project?.assembly?.clips || [];
  if (!clips.length) return;
  const zoom = el._zoom;
  const totalOut = state.edl?.total_duration || state.project?.sources?.[0]?.duration || 60;

  clips.forEach((clip, idx) => {
    const start = (clip.output_start ?? (idx / clips.length) * totalOut);
    const dur = clip.duration ?? (totalOut / clips.length);
    const block = document.createElement("div");
    block.className = "tl-clip";
    block.draggable = true;
    block.dataset.idx = idx;
    block.style.left = `${start * zoom}px`;
    block.style.width = `${Math.max(4, dur * zoom)}px`;
    const name = clip.name || clip.source_id || `Clip ${idx + 1}`;
    block.innerHTML = `<span class="tl-clip-lbl">${name}</span>`;
    block.title = name;
    block.addEventListener("click", (e) => { e.stopPropagation(); selectClip(el, block, idx); });
    wireDrag(block, el, clips);
    el.appendChild(block);
  });
}

function selectClip(el, block, idx) {
  el.querySelectorAll(".tl-clip.selected").forEach((b) => b.classList.remove("selected"));
  block.classList.toggle("selected");
  el._selectedIdx = block.classList.contains("selected") ? idx : null;
}

function wireDrag(block, el, clips) {
  let dragIdx = null;
  block.addEventListener("dragstart", (e) => {
    dragIdx = +block.dataset.idx;
    block.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
  });
  block.addEventListener("dragend", () => block.classList.remove("dragging"));

  el.addEventListener("dragover", (e) => { e.preventDefault(); e.dataTransfer.dropEffect = "move"; });

  el.addEventListener("drop", async (e) => {
    e.preventDefault();
    if (dragIdx == null) return;
    const r = el.getBoundingClientRect();
    const x = e.clientX - r.left;
    const targetT = x / el._zoom;
    const arr = [...clips];
    const [moved] = arr.splice(dragIdx, 1);
    const insertAt = arr.findIndex((c) => (c.output_start ?? 0) > targetT);
    arr.splice(insertAt === -1 ? arr.length : insertAt, 0, moved);
    try {
      const updated = await post("/assembly/reorder", { clips: arr });
      if (updated) setState({ project: updated });
      renderBroll(el);
      el._flashSaved();
    } catch (err) { toast(String(err.message || err), "danger"); }
    dragIdx = null;
  });
}

export async function importBrollClip(el, copy) {
  openFileBrowser({
    title: copy.import,
    filter: (e) => /\.(mp4|mov|mkv|webm|avi|m4v|mxf|mp3|wav|m4a|aac)$/i.test(e.name),
    onPick: async (path) => {
      try {
        const updated = await post("/assembly/import", { path });
        if (updated) setState({ project: updated });
        renderBroll(el);
        el._flashSaved();
      } catch (err) { toast(String(err.message || err), "danger"); }
    },
    onCancel: () => {},
  });
}

export async function deleteSelectedClip(el, flashSaved) {
  if (el._selectedIdx == null) return;
  const clips = state.project?.assembly?.clips || [];
  const clip = clips[el._selectedIdx];
  if (!clip) return;
  try {
    const updated = await post("/assembly/remove", { id: clip.id ?? clip.source_id });
    if (updated) setState({ project: updated });
    renderBroll(el);
    flashSaved();
  } catch (err) { toast(String(err.message || err), "danger"); }
}
