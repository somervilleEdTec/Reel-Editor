import { get, post } from "../../api.js";
import { toast } from "../../components/toast.js";

/**
 * Curated free-music browser: preview samples, download to local library,
 * and attach as the project music bed.
 *
 * onUsed({ sources, audio, source, track }) — after "Use in project"
 */
export function openMusicLibrary({ copy, onUsed, onCancel } = {}) {
  const c = copy || {};
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  const modal = document.createElement("div");
  modal.className = "modal music-modal";
  modal.setAttribute("role", "dialog");
  modal.setAttribute("aria-modal", "true");
  modal.innerHTML = `
    <div class="music-title-row">
      <h2 class="display" style="font-size:1.25rem">${c.musicLibraryTitle || "Music library"}</h2>
      <button type="button" class="secondary music-close" aria-label="${c.close || "Close"}">×</button>
    </div>
    <p class="music-hint">${c.musicLibraryHint || ""}</p>
    <div class="music-toolbar">
      <label class="field music-genre-field">${c.musicGenre || "Genre"}
        <select class="music-genre"><option value="">${c.musicAllGenres || "All"}</option></select>
      </label>
      <div class="music-tabs" role="tablist">
        <button type="button" class="chip music-tab on" data-tab="catalog">${c.musicCatalogTab || "Catalog"}</button>
        <button type="button" class="chip music-tab" data-tab="library">${c.musicMyLibraryTab || "My library"}</button>
      </div>
    </div>
    <div class="music-list" role="list"></div>
    <p class="music-note mono"></p>
    <audio class="music-preview" preload="none"></audio>
  `;
  backdrop.appendChild(modal);
  document.body.appendChild(backdrop);

  const listEl = modal.querySelector(".music-list");
  const genreEl = modal.querySelector(".music-genre");
  const noteEl = modal.querySelector(".music-note");
  const audio = modal.querySelector(".music-preview");
  let tab = "catalog";
  let catalog = { tracks: [], genres: [], attribution_note: "" };
  let playingId = null;

  const close = () => {
    audio.pause();
    backdrop.remove();
    onCancel?.();
  };
  modal.querySelector(".music-close").onclick = close;
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) close();
  });

  modal.querySelectorAll(".music-tab").forEach((btn) => {
    btn.onclick = () => {
      tab = btn.dataset.tab;
      modal.querySelectorAll(".music-tab").forEach((b) => b.classList.toggle("on", b === btn));
      renderList();
    };
  });
  genreEl.onchange = () => renderList();

  function fmtDur(s) {
    const n = Math.round(Number(s) || 0);
    return `${Math.floor(n / 60)}:${String(n % 60).padStart(2, "0")}`;
  }

  function stopPreview() {
    audio.pause();
    audio.removeAttribute("src");
    playingId = null;
    listEl.querySelectorAll(".music-play").forEach((b) => {
      b.textContent = c.musicPreview || "Preview";
      b.classList.remove("playing");
    });
  }

  async function togglePreview(track, btn) {
    if (playingId === track.id && !audio.paused) {
      stopPreview();
      return;
    }
    stopPreview();
    playingId = track.id;
    btn.textContent = c.musicStop || "Stop";
    btn.classList.add("playing");
    audio.src = `/music/preview/${encodeURIComponent(track.id)}`;
    try {
      await audio.play();
    } catch {
      toast(c.musicPreviewFail || "Could not play preview", "danger");
      stopPreview();
    }
  }
  audio.addEventListener("ended", stopPreview);

  async function downloadTrack(track, btn) {
    btn.disabled = true;
    const prev = btn.textContent;
    btn.textContent = c.musicDownloading || "Downloading…";
    try {
      await post("/music/download", { track_id: track.id });
      track.downloaded = true;
      toast(c.musicDownloaded || "Saved to library");
      renderList();
    } catch (e) {
      toast(e.message || c.musicDownloadFail || "Download failed", "danger");
      btn.disabled = false;
      btn.textContent = prev;
    }
  }

  async function useTrack(track, btn) {
    btn.disabled = true;
    const prev = btn.textContent;
    btn.textContent = c.musicUsing || "Adding…";
    try {
      const result = await post("/music/use", { track_id: track.id });
      toast(c.musicUsed || "Music added to project");
      stopPreview();
      backdrop.remove();
      onUsed?.(result);
    } catch (e) {
      toast(e.message || c.musicUseFail || "Could not add music", "danger");
      btn.disabled = false;
      btn.textContent = prev;
    }
  }

  function renderList() {
    const genre = genreEl.value;
    let tracks = tab === "library"
      ? (catalog._library || []).slice()
      : (catalog.tracks || []).slice();
    if (genre) tracks = tracks.filter((t) => t.genre === genre);
    noteEl.textContent = catalog.attribution_note || "";
    if (!tracks.length) {
      listEl.innerHTML = `<p class="music-empty">${
        tab === "library"
          ? (c.musicLibraryEmpty || "No downloaded tracks yet.")
          : (c.musicCatalogEmpty || "No tracks match.")
      }</p>`;
      return;
    }
    listEl.innerHTML = "";
    for (const track of tracks) {
      const row = document.createElement("div");
      row.className = "music-row";
      row.setAttribute("role", "listitem");
      row.innerHTML = `
        <div class="music-meta">
          <strong class="music-title">${escapeHtml(track.title)}</strong>
          <span class="music-sub">${escapeHtml(track.artist)} · ${escapeHtml(track.genre)} · ${fmtDur(track.duration_s)}</span>
          <span class="music-license">${escapeHtml(track.license)} — ${escapeHtml(track.attribution || "")}</span>
        </div>
        <div class="music-actions">
          <button type="button" class="secondary music-play">${c.musicPreview || "Preview"}</button>
          ${
            track.downloaded
              ? `<button type="button" class="secondary music-dl" disabled>${c.musicInLibrary || "In library"}</button>`
              : `<button type="button" class="secondary music-dl">${c.musicDownload || "Download"}</button>`
          }
          <button type="button" class="music-use">${c.musicUse || "Use in project"}</button>
        </div>`;
      row.querySelector(".music-play").onclick = (e) => togglePreview(track, e.currentTarget);
      const dl = row.querySelector(".music-dl");
      if (!track.downloaded) dl.onclick = (e) => downloadTrack(track, e.currentTarget);
      row.querySelector(".music-use").onclick = (e) => useTrack(track, e.currentTarget);
      listEl.appendChild(row);
    }
  }

  (async () => {
    try {
      const [cat, lib] = await Promise.all([get("/music/catalog"), get("/music/library")]);
      catalog = cat;
      catalog._library = lib.tracks || [];
      const downloaded = new Set(catalog._library.map((t) => t.id));
      for (const t of catalog.tracks || []) t.downloaded = downloaded.has(t.id);
      for (const g of cat.genres || []) {
        genreEl.appendChild(new Option(g, g));
      }
      renderList();
    } catch (e) {
      listEl.innerHTML = `<p class="music-empty">${escapeHtml(e.message || "Failed to load catalog")}</p>`;
    }
  })();
}

function escapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
