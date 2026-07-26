import { get, post } from "../api.js";
import { setState } from "../store.js";
import { navigate } from "../router.js";
import { openFileBrowser } from "../components/filebrowser.js";
import { toast } from "../components/toast.js";

export async function renderSetup(root, state) {
  const c = state.copy.setup;
  let status = state.setup || (await get("/setup/status"));
  setState({ setup: status });

  root.innerHTML = `<div class="view setup">
    <h1 class="hero-brand">${state.copy.brand}</h1>
    <p class="tagline">${c.tagline}</p>
    <div class="setup-steps"></div>
    <div class="setup-actions">
      <button type="button" class="start" ${status.ffmpeg?.found && status.projects_writable ? "" : "disabled"}>${c.start}</button>
    </div>
  </div>`;

  const steps = root.querySelector(".setup-steps");
  steps.appendChild(stepRow(1, c.ffmpeg.title, ffmpegBody(status, c, refresh), !status.ffmpeg?.found));
  steps.appendChild(stepRow(2, c.model.title, modelBody(status, c, refresh), status.ffmpeg?.found && !status.model?.consented));
  steps.appendChild(stepRow(3, c.projects.title, projectsBody(status, c, refresh), status.ffmpeg?.found));

  root.querySelector(".start").onclick = async () => {
    try {
      await post("/setup/complete", {});
      const next = await get("/setup/status");
      setState({ setup: next });
      navigate("home");
    } catch (e) {
      toast(String(e.message || e), "danger");
    }
  };

  async function refresh() {
    status = await get("/setup/status");
    setState({ setup: status });
    renderSetup(root, { ...state, setup: status });
  }
}

function stepRow(n, title, body, active) {
  const el = document.createElement("div");
  el.className = `setup-step${active ? " active" : ""}`;
  el.innerHTML = `<div class="setup-num">${n}</div><div class="setup-body"><div class="section-label">${title}</div></div>`;
  el.querySelector(".setup-body").appendChild(body);
  return el;
}

function ffmpegBody(status, c, refresh) {
  const wrap = document.createElement("div");
  if (status.ffmpeg?.found) {
    wrap.innerHTML = `<p>${c.ffmpeg.ok}</p><p class="mono">${status.ffmpeg.version || ""}</p>`;
  } else {
    wrap.innerHTML = `<p>${c.ffmpeg.missing}</p><button type="button" class="secondary retry">${c.ffmpeg.retry}</button>`;
    wrap.querySelector(".retry").onclick = refresh;
  }
  return wrap;
}

function modelBody(status, c, refresh) {
  const wrap = document.createElement("div");
  wrap.innerHTML = `<div class="consent md"></div>
    <label style="display:flex;gap:.5rem;align-items:center;margin:.75rem 0">
      <input type="checkbox" class="consent-box" ${status.model?.consented ? "checked" : ""}/>
      ${c.model.consent}
    </label>
    <div style="display:flex;gap:.5rem;flex-wrap:wrap">
      <button type="button" class="download">${c.model.download}</button>
      <button type="button" class="secondary skip">${c.model.skip}</button>
    </div>`;
  fetch("/content/consent.md").then((r) => r.text()).then((t) => {
    wrap.querySelector(".consent").textContent = t;
  });
  wrap.querySelector(".download").onclick = async () => {
    await post("/setup/consent", { consented: true });
    toast("Model consent saved");
    refresh();
  };
  wrap.querySelector(".skip").onclick = refresh;
  wrap.querySelector(".consent-box").onchange = async (e) => {
    await post("/setup/consent", { consented: e.target.checked });
    refresh();
  };
  return wrap;
}

function projectsBody(status, c, refresh) {
  const wrap = document.createElement("div");
  wrap.innerHTML = `<p class="mono path">${status.projects_dir || ""}</p>
    <p>${c.projects.hint}</p>
    <button type="button" class="secondary change">${c.projects.change}</button>`;
  wrap.querySelector(".change").onclick = () => {
    openFileBrowser({
      title: c.projects.title,
      startDir: status.projects_dir,
      filter: () => false,
      allowDirs: true,
      onPick: async (path) => {
        try {
          await post("/setup/projects-dir", { path });
          refresh();
        } catch (e) {
          toast(String(e.message || e), "danger");
        }
      },
    });
  };
  return wrap;
}
