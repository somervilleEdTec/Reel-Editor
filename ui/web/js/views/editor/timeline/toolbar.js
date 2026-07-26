import { post, get } from "../../../api.js";
import { state, setState } from "../../../store.js";
import { toast } from "../../../components/toast.js";
import { importBrollClip } from "./broll-track.js";
import { addMarkerAtTime } from "./markers.js";

export function wireToolbar(el, ctx) {
  const { copy, brollEl, markersEl, flashSaved, onUndo, onRedo, onZoom, blade, restore } = ctx;

  el.querySelector("[data-a=blade]").onclick = blade;
  el.querySelector("[data-a=restore]").onclick = restore;

  el.querySelector("[data-a=import]").onclick = () => importBrollClip(brollEl, copy);

  el.querySelector("[data-a=distribute]").onclick = async () => {
    try {
      const updated = await post("/assembly/distribute", {});
      if (updated) setState({ project: updated });
      toast(copy.distributeOk || "Clips distributed", "ok");
      flashSaved();
    } catch (err) { toast(String(err.message || err), "danger"); }
  };

  el.querySelector("[data-a=cleanup]").onclick = async () => {
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
  };

  el.querySelector("[data-a=marker]").onclick = () => {
    const t = state.playheadOut || 0;
    addMarkerAtTime(markersEl, t);
    toast(copy.markerAdded, "ok");
  };

  el.querySelector("[data-a=undo]").onclick = onUndo;
  el.querySelector("[data-a=redo]").onclick = onRedo;
  el.querySelector("[data-a=zoom-in]").onclick = () => onZoom(1);
  el.querySelector("[data-a=zoom-out]").onclick = () => onZoom(-1);
}
