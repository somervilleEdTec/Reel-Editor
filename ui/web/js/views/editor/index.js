import { get, post } from "../../api.js";
import { setState, state } from "../../store.js";
import { toast } from "../../components/toast.js";
import { mountTranscript } from "./transcript.js";
import { mountStage } from "./stage.js";
import { mountInspector } from "./inspector.js";
import { mountMediaBin } from "./media_bin.js";
import { openExport } from "./export.js";
import { navigate } from "../../router.js";
import { mountTimeline } from "./timeline/index.js";
import { outToSrc } from "./timeline/edl-utils.js";
import { registerEditorShortcuts, unregisterEditorShortcuts } from "../../shortcuts.js";

export async function renderEditor(root, st) {
  let project = st.project;
  if (!project) {
    try {
      project = await get("/project");
      setState({ project });
    } catch {
      navigate("home");
      return;
    }
  }
  const setup = st.setup || (await get("/setup/status"));
  setState({ setup });
  if (!st.presets) setState({ presets: await get("/captions/presets") });
  if (!st.safezones) setState({ safezones: await get("/safezones") });

  const c = st.copy.editor;
  const ct = st.copy.timeline;
  const name = (st.projectPath || "project.json").split(/[/\\]/).slice(-2, -1)[0] || "Reel";

  root.innerHTML = `<div class="editor-shell">
    <header class="topbar">
      <a href="#/home" class="mark">${st.copy.brand}</a>
      <span class="proj-name">${name}</span>
      <span class="saved">${c.saved} ✓</span>
      <span class="spacer"></span>
      <button type="button" class="secondary undo-btn" title="Undo (⌘Z)">${ct.undo}</button>
      <button type="button" class="secondary redo-btn" title="Redo (⌘⇧Z)">${ct.redo}</button>
      <button type="button" class="accent export-btn" ${setup.ffmpeg?.found ? "" : "disabled"}>${c.export}</button>
    </header>
    <div class="banner-slot"></div>
    <div class="editor-grid">
      <aside class="panel left-panel">
        <div class="panel-tabs" role="tablist">
          <button type="button" class="panel-tab active" role="tab" data-tab="media">${c.mediaTab}</button>
          <button type="button" class="panel-tab" role="tab" data-tab="transcript">${c.transcriptTab}</button>
        </div>
        <div class="rail media-rail" role="tabpanel"></div>
        <div class="rail transcript-rail" role="tabpanel" hidden></div>
      </aside>
      <section class="panel panel-stage">
        <div class="panel-head">${c.panelPreview}</div>
        <div class="stage-wrap"></div>
      </section>
      <aside class="panel">
        <div class="panel-head">${c.panelProps}</div>
        <div class="rail inspector"></div>
      </aside>
    </div>
    <div class="timeline-zone"></div>
  </div>`;

  if (!setup.ffmpeg?.found) {
    const slot = root.querySelector(".banner-slot");
    slot.innerHTML = `<div class="banner">${c.ffmpegBanner} <a href="#/setup">${c.fixSetup}</a></div>`;
  }

  const flashSaved = () => {
    const el = root.querySelector(".saved");
    el.classList.add("show");
    clearTimeout(flashSaved._t);
    flashSaved._t = setTimeout(() => el.classList.remove("show"), 1200);
  };

  // Left rail tabs
  root.querySelectorAll(".panel-tab").forEach((btn) => {
    btn.onclick = () => {
      root.querySelectorAll(".panel-tab").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const tab = btn.dataset.tab;
      root.querySelector(".media-rail").hidden = tab !== "media";
      root.querySelector(".transcript-rail").hidden = tab !== "transcript";
    };
  });

  mountMediaBin(root.querySelector(".media-rail"), { copy: c, flashSaved });
  mountTranscript(root.querySelector(".transcript-rail"), { copy: c, flashSaved });
  mountStage(root.querySelector(".stage-wrap"), { copy: c, flashSaved });
  mountInspector(root.querySelector(".inspector"), { copy: c, flashSaved });
  root.querySelector(".export-btn").onclick = () => openExport({ copy: st.copy.export, flashSaved });

  const getVideo = () => root.querySelector(".stage-wrap")._video ?? root.querySelector(".stage-video");

  const onSeekOutput = (outTime) => {
    const segs = state.edl?.segments;
    const srcTime = segs?.length ? (outToSrc(outTime, segs) ?? outTime) : outTime;
    const v = getVideo();
    if (v) v.currentTime = srcTime;
    setState({ playheadOut: outTime, playheadSrc: srcTime });
  };

  const timelineEl = root.querySelector(".timeline-zone");
  mountTimeline(timelineEl, { copy: ct, flashSaved, getVideo, onSeekOutput });

  // Topbar undo/redo
  const undoAct = async () => {
    try { await post("/project/undo", {}); const p = await get("/project"); setState({ project: p }); const e = await get("/edl").catch(() => null); if (e) setState({ edl: e }); flashSaved(); } catch (err) { toast(String(err.message || err), "danger"); }
  };
  const redoAct = async () => {
    try { await post("/project/redo", {}); const p = await get("/project"); setState({ project: p }); const e = await get("/edl").catch(() => null); if (e) setState({ edl: e }); flashSaved(); } catch (err) { toast(String(err.message || err), "danger"); }
  };
  root.querySelector(".undo-btn").onclick = undoAct;
  root.querySelector(".redo-btn").onclick = redoAct;

  // Keyboard shortcuts
  registerEditorShortcuts({
    getVideo,
    blade: () => timelineEl._blade?.(),
    undo: undoAct,
    redo: redoAct,
    zoomIn: () => timelineEl.querySelector("[data-a=zoom-in]")?.click(),
    zoomOut: () => timelineEl.querySelector("[data-a=zoom-out]")?.click(),
    showHelp: () => {
      import("../../components/toast.js").then(({ toast: t }) => t(ct.shortcutsHint, "ok"));
    },
    deleteSelected: () => timelineEl._deleteSelected?.(),
  });

  // Unregister shortcuts when navigating away
  window.addEventListener("hashchange", unregisterEditorShortcuts, { once: true });
}
