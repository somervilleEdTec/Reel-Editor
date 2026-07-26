import { post, get, del } from "../../../api.js";
import { state, setState } from "../../../store.js";
import { toast } from "../../../components/toast.js";
import { openFileBrowser } from "../../../components/filebrowser.js";
import { isVideoName } from "../../../formats.js";

export function mountBrollTrack(el, { zoom, flashSaved }) {
  el._zoom = zoom;
  el._flashSaved = flashSaved;
  renderBroll(el);
}

export function refreshBrollTrack(el, zoom) {
  if (zoom != null) el._zoom = zoom;
  renderBroll(el);
}

function clipSpan(clip, words, edl) {
  const startW = words.find((w) => w.id === clip.word_start_id);
  const endW = words.find((w) => w.id === clip.word_end_id);
  const segs = edl?.segments || [];
  if (!startW || !endW || !segs.length) {
    return { start: 0, dur: Math.max(0.5, edl?.total_duration || 2) };
  }
  const o0 = segs.find((s) => startW.start_s >= s.source_start && startW.start_s <= s.source_end);
  const o1 = segs.find((s) => endW.end_s >= s.source_start && endW.end_s <= s.source_end);
  const start = o0
    ? o0.output_start + (startW.start_s - o0.source_start)
    : 0;
  const end = o1
    ? o1.output_start + (endW.end_s - o1.source_start)
    : start + 1;
  return { start, dur: Math.max(0.2, end - start) };
}

function renderBroll(el) {
  el.innerHTML = "";
  const clips = state.project?.assembly?.clips || [];
  if (!clips.length) return;
  const zoom = el._zoom;
  const words = state.project?.words || [];
  const edl = state.edl;

  clips.forEach((clip, idx) => {
    const { start, dur } = clipSpan(clip, words, edl);
    const block = document.createElement("div");
    block.className = "tl-clip";
    block.draggable = true;
    block.dataset.idx = idx;
    block.dataset.id = clip.id;
    block.style.left = `${start * zoom}px`;
    block.style.width = `${Math.max(4, dur * zoom)}px`;
    const name = clip.id || clip.source_id || `Clip ${idx + 1}`;
    block.innerHTML = `<span class="tl-clip-lbl">${name}</span>`;
    block.title = name;
    block.addEventListener("click", (e) => {
      e.stopPropagation();
      selectClip(el, block, idx);
    });
    wireDrag(block, el);
    el.appendChild(block);
  });
}

function selectClip(el, block, idx) {
  el.querySelectorAll(".tl-clip.selected").forEach((b) => b.classList.remove("selected"));
  block.classList.add("selected");
  el._selectedIdx = idx;
}

function wireDrag(block, el) {
  block.addEventListener("dragstart", (e) => {
    el._dragId = block.dataset.id;
    block.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
  });
  block.addEventListener("dragend", () => block.classList.remove("dragging"));
  if (el._dropWired) return;
  el._dropWired = true;
  el.addEventListener("dragover", (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  });
  el.addEventListener("drop", async (e) => {
    e.preventDefault();
    const dragId = el._dragId;
    if (!dragId) return;
    const clips = state.project?.assembly?.clips || [];
    const ids = clips.map((c) => c.id);
    const from = ids.indexOf(dragId);
    if (from < 0) return;
    const r = el.getBoundingClientRect();
    const x = e.clientX - r.left;
    const blocks = [...el.querySelectorAll(".tl-clip")];
    let insertAt = blocks.length;
    for (let i = 0; i < blocks.length; i++) {
      const mid = blocks[i].offsetLeft + blocks[i].offsetWidth / 2;
      if (x < mid) {
        insertAt = i;
        break;
      }
    }
    ids.splice(from, 1);
    if (insertAt > from) insertAt -= 1;
    ids.splice(insertAt, 0, dragId);
    try {
      const assembly = await post("/assembly/reorder", { order: ids });
      const project = { ...state.project, assembly };
      setState({ project });
      renderBroll(el);
      el._flashSaved();
    } catch (err) {
      toast(String(err.message || err), "danger");
    }
    el._dragId = null;
  });
}

export async function importBrollClip(el, copy) {
  openFileBrowser({
    title: copy.import,
    filter: (e) => e.type === "dir" || isVideoName(e.name),
    onPickMany: async (paths) => {
      try {
        await post("/assembly/import", { paths });
        const assembly = await post("/assembly/distribute", {});
        const project = await get("/project");
        setState({ project: { ...project, assembly } });
        renderBroll(el);
        el._flashSaved();
      } catch (err) {
        toast(String(err.message || err), "danger");
      }
    },
    onPick: async (path) => {
      try {
        await post("/assembly/import", { paths: [path] });
        const assembly = await post("/assembly/distribute", {});
        const project = await get("/project");
        setState({ project: { ...project, assembly } });
        renderBroll(el);
        el._flashSaved();
      } catch (err) {
        toast(String(err.message || err), "danger");
      }
    },
    onCancel: () => {},
  });
}

export async function deleteSelectedClip(el, flashSaved) {
  if (el._selectedIdx == null) return;
  const clips = state.project?.assembly?.clips || [];
  const clip = clips[el._selectedIdx];
  if (!clip?.id) return;
  try {
    await del(`/assembly/clip/${encodeURIComponent(clip.id)}`);
    const project = await get("/project");
    setState({ project });
    renderBroll(el);
    flashSaved();
  } catch (err) {
    toast(String(err.message || err), "danger");
  }
}
