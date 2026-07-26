import { get, post } from "../api.js";
import { setState } from "../store.js";
import { navigate } from "../router.js";
import { openFileBrowser, looksLikePath } from "../components/filebrowser.js";
import { isVideoName } from "../formats.js";
import { progressBar, setProgress } from "../components/progress.js";
import { toast } from "../components/toast.js";

export async function renderHome(root, state) {
  const c = state.copy.home;
  const list = await get("/projects");
  root.innerHTML = `<div class="view home">
    <h1 class="hero-brand">${state.copy.brand}</h1>
    <p class="tagline">${c.tagline}</p>
    <div class="home-actions"><button type="button" class="new">${c.new}</button></div>
    <div class="create-progress" hidden></div>
    <div class="recents"></div>
  </div>`;

  const recents = root.querySelector(".recents");
  if (!list.projects?.length) {
    recents.innerHTML = `<div class="empty-state">
      <h2 class="display" style="font-size:1.5rem">${c.emptyTitle}</h2>
      <p class="tagline">${c.emptyBody}</p>
    </div>`;
  } else {
    recents.innerHTML = `<p class="section-label">${c.recent}</p><ul class="recent-list"></ul>`;
    const ul = recents.querySelector("ul");
    for (const p of list.projects) {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.innerHTML = `<strong>${p.name}</strong><div class="mono">${p.path}</div>`;
      btn.onclick = async () => {
        try {
          const project = await post("/project/open", { path: p.path });
          setState({ project, projectPath: p.path });
          navigate("editor");
        } catch (e) {
          toast(String(e.message || e), "danger");
        }
      };
      li.appendChild(btn);
      ul.appendChild(li);
    }
  }

  root.querySelector(".new").onclick = () => {
    openFileBrowser({
      title: c.new,
      filter: (e) => isVideoName(e.name),
      onPick: (videoPath) => createReel(root, videoPath),
    });
  };
}

async function createReel(root, videoPath) {
  if (!looksLikePath(videoPath) || !isVideoName(videoPath)) {
    toast("Choose a video file from the browser, or paste a full video path.", "danger");
    return;
  }
  const box = root.querySelector(".create-progress");
  box.hidden = false;
  box.innerHTML = "";
  const bar = progressBar(0.05, true);
  box.appendChild(bar);
  try {
    const { job_id, path } = await post("/projects/create", { video_path: videoPath });
    await pollJob(job_id, (j) => setProgress(bar, j.progress || 0.1, j.status === "running"));
    const project = await post("/project/open", { path });
    setState({ project, projectPath: path });
    navigate("editor");
  } catch (e) {
    toast(String(e.message || e), "danger");
  }
}

async function pollJob(id, onTick) {
  for (;;) {
    const j = await get(`/jobs/${id}`);
    onTick?.(j);
    if (j.status === "done") return j;
    if (j.status === "error") throw new Error(j.error || "Job failed");
    if (j.status === "cancelled") throw new Error("Cancelled");
    await new Promise((r) => setTimeout(r, 500));
  }
}
