import { get, post } from "../../api.js";
import { state } from "../../store.js";
import { openSheet } from "../../components/sheet.js";
import { openFileBrowser } from "../../components/filebrowser.js";
import { progressBar, setProgress } from "../../components/progress.js";
import { toast } from "../../components/toast.js";
import { OUTPUT_FORMATS, VIDEO_EXTS } from "../../formats.js";

// Only strip known media extensions — never dotted name parts like "take.2".
const MEDIA_EXT_RE = new RegExp(`\\.(${VIDEO_EXTS.join("|")})$`, "i");

export async function openExport({ copy }) {
  let formats = OUTPUT_FORMATS;
  try {
    formats = (await get("/formats")).output;
  } catch {
    /* offline fallback */
  }

  const body = document.createElement("div");
  body.innerHTML = `<label class="field">${copy.filename}
      <input class="mono out" value="master.mp4" />
    </label>
    <p class="section-label">${copy.format}</p>
    <div class="seg fmt-seg" style="grid-template-columns:repeat(${formats.length},1fr)">
      ${formats.map((f, i) => `<button type="button" data-fmt="${f.key}" title="${f.label}" class="${i === 0 ? "active" : ""}">${f.key.toUpperCase()}</button>`).join("")}
    </div>
    <p class="section-label" style="margin-top:.75rem">${copy.aspect}</p>
    <div class="seg">
      <button type="button" class="active" data-aspect="portrait_9_16">${copy.portrait}</button>
      <button type="button" data-aspect="landscape_16_9">${copy.landscape}</button>
    </div>
    <p class="section-label" style="margin-top:.75rem">${copy.destination}</p>
    <div class="dest-row">
      <span class="mono dest-label">${copy.projectFolder}</span>
      <button type="button" class="secondary choose-dir">${copy.chooseFolder}</button>
    </div>
    <div class="export-actions" style="margin-top:1rem;display:flex;gap:.5rem;flex-wrap:wrap">
      <button type="button" class="accent run">${copy.run}</button>
      <button type="button" class="secondary cancel-run" hidden>${copy.cancel}</button>
    </div>
    <div class="export-status" style="margin-top:1rem" aria-live="polite"></div>`;

  const outInput = body.querySelector(".out");
  let format = formats[0]?.key || "mp4";
  let aspect = "portrait_9_16";
  let destDir = null;

  body.querySelectorAll("[data-fmt]").forEach((btn) => {
    btn.onclick = () => {
      body.querySelectorAll("[data-fmt]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      format = btn.dataset.fmt;
      const ext = formats.find((f) => f.key === format)?.ext || `.${format}`;
      const base = outInput.value.trim().replace(MEDIA_EXT_RE, "") || "master";
      outInput.value = base + ext;
    };
  });
  body.querySelectorAll("[data-aspect]").forEach((btn) => {
    btn.onclick = () => {
      body.querySelectorAll("[data-aspect]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      aspect = btn.dataset.aspect;
    };
  });
  body.querySelector(".choose-dir").onclick = () => {
    openFileBrowser({
      title: state.copy?.filebrowser?.titleFolder || copy.chooseFolder,
      startDir: destDir,
      filter: () => false,
      allowDirs: true,
      onPick: (dir) => {
        destDir = dir;
        body.querySelector(".dest-label").textContent = dir;
      },
    });
  };

  let sheetClosed = false;
  const sheet = openSheet(copy.title, body, { onClose: () => { sheetClosed = true; } });
  const runBtn = body.querySelector(".run");
  const cancelBtn = body.querySelector(".cancel-run");
  let jobId = null;

  runBtn.onclick = async () => {
    const name = outInput.value.trim() || "master";
    const sep = destDir?.includes("\\") ? "\\" : "/";
    const out = destDir ? `${destDir.replace(/[\\/]+$/, "")}${sep}${name}` : name;
    const status = body.querySelector(".export-status");
    status.innerHTML = "";
    const bar = progressBar(0.05, true);
    status.appendChild(bar);
    runBtn.disabled = true;
    runBtn.textContent = copy.exporting;
    cancelBtn.hidden = false;
    cancelBtn.disabled = false;
    cancelBtn.onclick = async () => {
      cancelBtn.disabled = true;
      if (jobId) await post(`/jobs/${jobId}/cancel`, {});
    };
    const finish = () => {
      runBtn.disabled = false;
      runBtn.textContent = copy.run;
      cancelBtn.hidden = true;
      jobId = null;
    };
    try {
      const res = await post("/jobs/export", { out, aspect, format });
      jobId = res.job_id;
      for (;;) {
        if (sheetClosed) return finish(); // sheet gone — stop polling, job finishes server-side
        const j = await get(`/jobs/${jobId}`);
        setProgress(bar, j.progress || 0.1, j.status === "running");
        if (j.status === "done") {
          setProgress(bar, 1, false);
          const full = j.result?.out || res.out || out;
          status.innerHTML = `<p>${copy.done}</p>
            <p class="section-label" style="margin:.5rem 0 .15rem">${copy.savedTo}</p>
            <p class="mono out-path"></p>
            <button type="button" class="copy">${copy.copyPath}</button>
            <button type="button" class="secondary close">${copy.close}</button>`;
          status.querySelector(".out-path").textContent = full;
          status.querySelector(".copy").onclick = () => {
            navigator.clipboard?.writeText(full);
            toast("Path copied");
          };
          status.querySelector(".close").onclick = () => sheet.close();
          return finish();
        }
        if (j.status === "error") {
          status.innerHTML = `<p class="toast danger" style="position:static">${j.error || "Error"}</p>
            <button type="button" class="copyd">${copy.copyDetails}</button>
            <button type="button" class="retry">${copy.retry}</button>`;
          status.querySelector(".copyd").onclick = () => navigator.clipboard?.writeText(j.error || "");
          status.querySelector(".retry").onclick = () => runBtn.click();
          return finish();
        }
        if (j.status === "cancelled") {
          toast(copy.cancelled, "danger");
          status.innerHTML = "";
          return finish();
        }
        await new Promise((r) => setTimeout(r, 500));
      }
    } catch (e) {
      toast(String(e.message || e), "danger");
      status.innerHTML = "";
      finish();
    }
  };
}
