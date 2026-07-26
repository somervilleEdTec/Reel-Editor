import { get, post } from "../../api.js";
import { progressBar, setProgress } from "../../components/progress.js";
import { toast } from "../../components/toast.js";
import { refreshProject, showError } from "./inspector_helpers.js";

export function mountInspectorReframe(el, { copy, flashSaved }) {
  el.innerHTML = `<div class="cluster">
    <p class="section-label">${copy.tools}</p>
    <button type="button" class="secondary clean-fillers">${copy.cleanFillers}</button>
    <label class="field">${copy.reframeMode}<select class="reframe-mode">
      <option value="active_speaker">${copy.reframeActive}</option>
      <option value="split_stacked">${copy.reframeSplit}</option>
      <option value="fixed">${copy.reframeFixed}</option>
    </select></label>
    <button type="button" class="secondary run-reframe">${copy.runReframe}</button>
    <div class="tool-status" aria-live="polite"></div>
  </div>`;
  el.querySelector(".clean-fillers").onclick = () => cleanFillers(el, copy, flashSaved);
  el.querySelector(".run-reframe").onclick = () => runReframe(el, flashSaved);
}

async function cleanFillers(root, copy, flashSaved) {
  const btn = root.querySelector(".clean-fillers");
  btn.disabled = true;
  try {
    const result = await post("/words/cleanup", {});
    await refreshProject(flashSaved);
    toast(`${result.deleted || 0} ${copy.fillersRemoved}`);
  } catch (e) {
    showError(e);
  } finally {
    btn.disabled = false;
  }
}

async function runReframe(root, flashSaved) {
  const btn = root.querySelector(".run-reframe");
  const status = root.querySelector(".tool-status");
  btn.disabled = true;
  status.innerHTML = "";
  const bar = progressBar(0.05, true);
  status.appendChild(bar);
  try {
    const { job_id } = await post("/jobs/reframe", {
      mode: root.querySelector(".reframe-mode").value,
    });
    if (job_id) await pollJob(job_id, bar);
    await refreshProject(flashSaved);
  } catch (e) {
    showError(e);
  } finally {
    btn.disabled = false;
    status.innerHTML = "";
  }
}

async function pollJob(jobId, bar) {
  for (;;) {
    const job = await get(`/jobs/${jobId}`);
    setProgress(bar, job.progress || 0.1, job.status === "running");
    if (job.status === "done") return;
    if (job.status === "error") throw new Error(job.error || "Failed");
    if (job.status === "cancelled") throw new Error("Cancelled");
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}
