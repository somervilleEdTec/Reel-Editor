import { get } from "../../api.js";
import { toast } from "../../components/toast.js";
import { setState, state } from "../../store.js";
import { paintCaption } from "./caption_preview.js";

export function showError(err) {
  toast(String(err.message || err), "danger");
}

export function commitProject(project, flashSaved) {
  setState({ project });
  flashSaved?.();
  refreshStage();
}

export async function refreshProject(flashSaved) {
  const project = await get("/project");
  commitProject(project, flashSaved);
  return project;
}

export function refreshStage() {
  const wrap = document.querySelector(".stage-wrap");
  if (wrap?._refreshStage) wrap._refreshStage();
  else {
    const cap = document.querySelector(".caption");
    if (cap) paintCaption(cap, state.project, state.presets || {});
  }
}

export function sourceLabel(src) {
  if (!src) return "";
  if (src.name) return src.name;
  if (src.path) return src.path.split(/[/\\]/).pop();
  return src.id || "";
}

export function formatSeconds(seconds) {
  const value = Number(seconds) || 0;
  return `${value.toFixed(value < 10 ? 1 : 0)}s`;
}
