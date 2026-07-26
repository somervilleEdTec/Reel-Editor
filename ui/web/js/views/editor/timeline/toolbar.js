import { post, get } from "../../../api.js";
import { state, setState } from "../../../store.js";
import { toast } from "../../../components/toast.js";
import { importBrollClip } from "./broll-track.js";
import { addMarkerAtTime } from "./markers.js";
import { getSelection } from "./selection.js";

export function wireToolbar(el, ctx) {
  const {
    copy, brollEl, markersEl, flashSaved,
    onUndo, onRedo, onZoom, onFit,
    setTool, getTool,
    split, restore, merge, deleteSelection, trimStart, trimEnd,
  } = ctx;

  const syncTool = () => {
    el.querySelectorAll("[data-tool]").forEach((b) => {
      b.classList.toggle("active", b.dataset.tool === getTool());
    });
    document.querySelector(".tl-canvas")?.classList.toggle("blade-mode", getTool() === "blade");
  };

  el.querySelector("[data-tool=select]").onclick = () => { setTool("select"); syncTool(); };
  el.querySelector("[data-tool=blade]").onclick = () => { setTool("blade"); syncTool(); };
  syncTool();

  el.querySelector("[data-a=split]").onclick = split;
  el.querySelector("[data-a=delete]").onclick = deleteSelection;
  el.querySelector("[data-a=restore]").onclick = restore;
  el.querySelector("[data-a=merge]").onclick = merge;
  el.querySelector("[data-a=trim-start]").onclick = trimStart;
  el.querySelector("[data-a=trim-end]").onclick = trimEnd;

  el.querySelector("[data-a=import]").onclick = () => importBrollClip(brollEl, copy);
  el.querySelector("[data-a=distribute]").onclick = async () => {
    try {
      const assembly = await post("/assembly/distribute", {});
      const project = await get("/project");
      setState({ project: { ...project, assembly } });
      toast(copy.distributeOk || "Clips distributed", "ok");
      flashSaved();
    } catch (err) { toast(String(err.message || err), "danger"); }
  };

  const more = el.querySelector("[data-a=more]");
  if (more) {
    more.onclick = () => {
      const panel = el.querySelector(".tl-more");
      if (panel) panel.hidden = !panel.hidden;
    };
  }
  el.querySelector("[data-a=cleanup]")?.addEventListener("click", async () => {
    try {
      const updated = await post("/words/cleanup", {});
      if (updated?.segments) setState({ edl: updated });
      else {
        const [proj, edl] = await Promise.all([get("/project"), get("/edl").catch(() => null)]);
        setState({ project: proj, ...(edl ? { edl } : {}) });
      }
      toast(copy.cleanDone, "ok");
      flashSaved();
    } catch (err) { toast(String(err.message || err), "danger"); }
  });
  el.querySelector("[data-a=marker]")?.addEventListener("click", () => {
    const t = state.playheadOut || 0;
    addMarkerAtTime(markersEl, t);
    toast(copy.markerAdded, "ok");
  });

  el.querySelector("[data-a=undo]").onclick = onUndo;
  el.querySelector("[data-a=redo]").onclick = onRedo;
  el.querySelector("[data-a=zoom-in]").onclick = () => onZoom(1);
  el.querySelector("[data-a=zoom-out]").onclick = () => onZoom(-1);
  el.querySelector("[data-a=fit]")?.addEventListener("click", () => onFit?.());

  const refreshEnabled = () => {
    const sel = getSelection();
    const hasSeg = sel.kind === "seg";
    const hasGap = sel.kind === "gap";
    const hasRange = sel.kind === "range";
    const hasClip = sel.kind === "clip";
    setDisabled(el, "delete", !(hasSeg || hasRange || hasClip));
    setDisabled(el, "restore", !hasGap);
    setDisabled(el, "merge", !hasGap);
    setDisabled(el, "trim-start", !hasSeg);
    setDisabled(el, "trim-end", !hasSeg);
  };
  document.addEventListener("tl-selection", refreshEnabled);
  refreshEnabled();
  el._refreshEnabled = refreshEnabled;
}

function setDisabled(root, action, disabled) {
  const btn = root.querySelector(`[data-a=${action}]`);
  if (btn) btn.disabled = disabled;
}
