import { get, post } from "../../api.js";
import { openSheet } from "../../components/sheet.js";
import { progressBar, setProgress } from "../../components/progress.js";
import { toast } from "../../components/toast.js";

export function openExport({ copy }) {
  const body = document.createElement("div");
  body.innerHTML = `<label class="field">${copy.filename}
      <input class="mono out" value="master.mp4" />
    </label>
    <p class="section-label">${copy.aspect}</p>
    <div class="seg">
      <button type="button" class="active" data-aspect="portrait_9_16">${copy.portrait}</button>
      <button type="button" data-aspect="landscape_16_9">${copy.landscape}</button>
    </div>
    <div class="export-actions" style="margin-top:1rem;display:flex;gap:.5rem;flex-wrap:wrap">
      <button type="button" class="accent run">${copy.run}</button>
    </div>
    <div class="export-status" style="margin-top:1rem"></div>`;

  let aspect = "portrait_9_16";
  body.querySelectorAll("[data-aspect]").forEach((btn) => {
    btn.onclick = () => {
      body.querySelectorAll("[data-aspect]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      aspect = btn.dataset.aspect;
    };
  });

  const sheet = openSheet(copy.title, body);
  let jobId = null;

  body.querySelector(".run").onclick = async () => {
    const out = body.querySelector(".out").value.trim() || "master.mp4";
    const status = body.querySelector(".export-status");
    status.innerHTML = "";
    const bar = progressBar(0.05, true);
    status.appendChild(bar);
    const cancelBtn = document.createElement("button");
    cancelBtn.type = "button";
    cancelBtn.className = "secondary";
    cancelBtn.textContent = copy.cancel;
    body.querySelector(".export-actions").appendChild(cancelBtn);
    cancelBtn.onclick = async () => {
      if (jobId) await post(`/jobs/${jobId}/cancel`, {});
    };
    try {
      const res = await post("/jobs/export", { out, aspect });
      jobId = res.job_id;
      for (;;) {
        const j = await get(`/jobs/${jobId}`);
        setProgress(bar, j.progress || 0.1, j.status === "running");
        if (j.status === "done") {
          setProgress(bar, 1, false);
          status.innerHTML = `<p>${copy.done}</p><p class="mono">${j.result?.out || out}</p>
            <button type="button" class="copy">${copy.copyPath}</button>
            <button type="button" class="secondary close">${copy.close}</button>`;
          status.querySelector(".copy").onclick = () => {
            navigator.clipboard?.writeText(j.result?.out || out);
            toast("Path copied");
          };
          status.querySelector(".close").onclick = () => sheet.close();
          cancelBtn.remove();
          return;
        }
        if (j.status === "error") {
          status.innerHTML = `<p class="toast danger" style="position:static">${j.error || "Error"}</p>
            <button type="button" class="copyd">${copy.copyDetails}</button>
            <button type="button" class="retry">${copy.retry}</button>`;
          status.querySelector(".copyd").onclick = () => navigator.clipboard?.writeText(j.error || "");
          status.querySelector(".retry").onclick = () => body.querySelector(".run").click();
          cancelBtn.remove();
          return;
        }
        if (j.status === "cancelled") {
          toast("Export cancelled", "danger");
          cancelBtn.remove();
          return;
        }
        await new Promise((r) => setTimeout(r, 500));
      }
    } catch (e) {
      toast(String(e.message || e), "danger");
      cancelBtn.remove();
    }
  };
}
