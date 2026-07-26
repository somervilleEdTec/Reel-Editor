import { get, post } from "../api.js";
import { state } from "../store.js";
import { crumbSegments, fmtSize, looksLikePath, normalizePastedPath } from "./fs_path.js";

/**
 * Media-library file browser: places sidebar, path bar, breadcrumbs,
 * icons/details, multi-select, paste-to-navigate-or-pick.
 *
 * Callbacks:
 *   onPick(path)           — single path (compat)
 *   onPickMany(paths[])    — preferred when set
 */
export function openFileBrowser({
  title,
  filter,
  startDir,
  pasteHint,
  onPick,
  onPickMany,
  onCancel,
  allowDirs = false,
  defaultView,
}) {
  const c = { ...(state.copy?.filebrowser || {}) };
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  const modal = document.createElement("div");
  modal.className = "modal fs-modal";
  modal.setAttribute("role", "dialog");
  modal.setAttribute("aria-modal", "true");
  modal.innerHTML = `
    <div class="fs-title-row">
      <h2 class="display" style="font-size:1.25rem">${title || c.title}</h2>
      <div class="fs-view-toggle" role="group" aria-label="${c.viewToggle || "View"}">
        <button type="button" class="fs-vbtn" data-view="icons" title="${c.largeIcons || "Large Icons"}">&#8862;</button>
        <button type="button" class="fs-vbtn" data-view="details" title="${c.details || "Details"}">&#9776;</button>
      </div>
    </div>
    <p class="fs-hint">${allowDirs ? c.hintFolder || "" : c.hintFile || ""}</p>
    <div class="fs-shell">
      <aside class="fs-places" aria-label="${c.places || "Places"}"></aside>
      <div class="fs-main">
        <div class="fs-toolbar">
          <button type="button" class="secondary fs-up" title="${c.up || "Up"}" disabled>↑</button>
          <form class="fs-path-form">
            <input class="fs-path mono" name="path" spellcheck="false" autocomplete="off"
              placeholder="${c.pathPlaceholder || "Folder path"}" />
            <button type="submit" class="secondary fs-go">${c.go || "Go"}</button>
          </form>
        </div>
        <nav class="fs-crumbs" aria-label="Path"></nav>
        <input class="fs-search" type="search" placeholder="${c.search || "Search this folder"}" />
        <ul class="fs-list" role="listbox" hidden></ul>
        <div class="fs-grid" role="listbox" hidden></div>
        <div class="fs-msg" hidden></div>
      </div>
    </div>
    <div class="fs-status" aria-live="polite"></div>
    <label class="field">${pasteHint || c.paste}
      <input class="mono paste" spellcheck="false" autocomplete="off" />
    </label>
    <div class="fs-actions">
      <button type="button" class="secondary cancel">${c.cancel}</button>
      <button type="button" class="secondary reveal" hidden>${c.reveal || "Reveal"}</button>
      ${allowDirs ? `<button type="button" class="use-dir">${c.useFolder || "Use this folder"}</button>` : ""}
      <button type="button" class="${allowDirs ? "secondary" : ""} open">${c.open}</button>
    </div>`;
  backdrop.appendChild(modal);
  document.body.appendChild(backdrop);

  const listEl = modal.querySelector(".fs-list");
  const gridEl = modal.querySelector(".fs-grid");
  const crumbs = modal.querySelector(".fs-crumbs");
  const placesEl = modal.querySelector(".fs-places");
  const msg = modal.querySelector(".fs-msg");
  const search = modal.querySelector(".fs-search");
  const paste = modal.querySelector(".paste");
  const pathInput = modal.querySelector(".fs-path");
  const statusEl = modal.querySelector(".fs-status");
  const revealBtn = modal.querySelector(".reveal");
  const upBtn = modal.querySelector(".fs-up");

  let current = startDir || null;
  let parentDir = null;
  let entries = [];
  let selectedSet = new Set();
  let lastClickIdx = -1;
  let viewMode = defaultView || "icons";
  let places = [];

  modal.querySelectorAll(".fs-vbtn").forEach((b) => {
    b.onclick = () => setViewMode(b.dataset.view);
  });

  function setViewMode(mode) {
    viewMode = mode;
    modal.querySelectorAll(".fs-vbtn").forEach((b) =>
      b.classList.toggle("active", b.dataset.view === mode)
    );
    listEl.hidden = mode !== "details";
    gridEl.hidden = mode !== "icons";
    renderView();
  }

  function close(cancelled) {
    backdrop.remove();
    document.removeEventListener("keydown", onKey, true);
    if (cancelled) onCancel?.();
  }

  function pick(paths) {
    const arr = Array.isArray(paths) ? paths.filter(Boolean) : [paths].filter(Boolean);
    if (!arr.length) {
      showMsg(c.needSelection || "Select a video, or paste a full file path.");
      return;
    }
    backdrop.remove();
    document.removeEventListener("keydown", onKey, true);
    if (onPickMany) onPickMany(arr);
    else if (onPick) onPick(arr[0]);
  }

  function visible() {
    const q = search.value.trim().toLowerCase();
    return entries.filter((e) => !q || e.name.toLowerCase().includes(q));
  }

  function selectedPaths() {
    const rows = visible();
    return [...selectedSet]
      .sort((a, b) => a - b)
      .map((i) => rows[i])
      .filter(Boolean)
      .map((e) => e.path);
  }

  function updateStatus() {
    const paths = selectedPaths();
    if (paths.length === 1) {
      statusEl.textContent = paths[0];
      paste.value = paths[0];
    } else if (paths.length > 1) {
      statusEl.textContent = `${paths.length} ${c.selectedCount || "files selected"}`;
      // Keep paste empty so Open never submits a status label as a path.
      paste.value = "";
    } else {
      statusEl.textContent = current ? `${c.browsing || "Browsing"} ${current}` : "";
    }
    revealBtn.hidden = paths.length !== 1;
    upBtn.disabled = !parentDir;
  }

  function showMsg(text) {
    msg.hidden = false;
    msg.textContent = text;
  }

  function handleClick(ev, idx, type, path) {
    if (type === "dir") {
      load(path);
      return;
    }
    if (ev.ctrlKey || ev.metaKey) {
      selectedSet.has(idx) ? selectedSet.delete(idx) : selectedSet.add(idx);
      lastClickIdx = idx;
    } else if (ev.shiftKey && lastClickIdx >= 0) {
      const lo = Math.min(lastClickIdx, idx);
      const hi = Math.max(lastClickIdx, idx);
      const rows = visible();
      for (let i = lo; i <= hi; i++) {
        if (rows[i]?.type === "file") selectedSet.add(i);
      }
    } else {
      selectedSet.clear();
      selectedSet.add(idx);
      lastClickIdx = idx;
    }
    updateStatus();
    renderView();
  }

  function renderCrumbs(dir) {
    crumbs.innerHTML = "";
    const frag = document.createDocumentFragment();
    const segs = crumbSegments(dir);
    segs.forEach((seg, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "fs-crumb";
      b.textContent = seg.label;
      if (i === segs.length - 1) b.setAttribute("aria-current", "true");
      b.onclick = () => load(seg.path);
      frag.appendChild(b);
      if (i < segs.length - 1) {
        const s = document.createElement("span");
        s.className = "fs-crumb-sep";
        s.textContent = "›";
        frag.appendChild(s);
      }
    });
    crumbs.appendChild(frag);
  }

  function renderPlaces() {
    placesEl.innerHTML = "";
    const heading = document.createElement("div");
    heading.className = "fs-places-label";
    heading.textContent = c.places || "Places";
    placesEl.appendChild(heading);
    for (const place of places) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "fs-place";
      b.textContent = place.label;
      b.title = place.path;
      b.classList.toggle("active", current === place.path);
      b.onclick = () => load(place.path);
      placesEl.appendChild(b);
    }
  }

  function renderDetails() {
    const rows = visible();
    listEl.innerHTML = "";
    msg.hidden = true;
    if (!rows.length) {
      showEmpty();
      return;
    }
    rows.forEach((e, i) => {
      const li = document.createElement("li");
      const b = document.createElement("button");
      b.type = "button";
      b.className = `fs-row ${e.type === "dir" ? "fs-dir" : "fs-file"}${selectedSet.has(i) ? " selected" : ""}`;
      b.setAttribute("role", "option");
      b.setAttribute("aria-selected", String(selectedSet.has(i)));
      const ext = e.type === "file" ? (e.name.match(/\.(\w+)$/)?.[1] || "").toUpperCase() : "";
      const size = e.type === "file" && e.size != null ? fmtSize(e.size) : "";
      b.innerHTML = `<span class="fs-icon" aria-hidden="true"></span>
        <span class="fs-name"></span>
        ${size ? `<span class="fs-size">${size}</span>` : ""}
        ${ext ? `<span class="fs-badge">${ext}</span>` : ""}`;
      b.querySelector(".fs-name").textContent = e.name;
      b.onclick = (ev) => handleClick(ev, i, e.type, e.path);
      b.ondblclick = () => {
        if (e.type === "file") pick([e.path]);
      };
      li.appendChild(b);
      listEl.appendChild(li);
    });
  }

  let thumbObserver = null;
  function getObserver() {
    if (!thumbObserver) {
      thumbObserver = new IntersectionObserver(
        (ents) => {
          ents.forEach((en) => {
            if (en.isIntersecting) {
              const img = en.target;
              img.src = img.dataset.src;
              thumbObserver.unobserve(img);
            }
          });
        },
        { rootMargin: "120px" }
      );
    }
    return thumbObserver;
  }

  function renderGrid() {
    const rows = visible();
    gridEl.innerHTML = "";
    msg.hidden = true;
    if (!rows.length) {
      showEmpty();
      return;
    }
    const obs = getObserver();
    rows.forEach((e, i) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `fs-tile ${e.type === "dir" ? "fs-dir" : "fs-file"}${selectedSet.has(i) ? " selected" : ""}`;
      btn.setAttribute("role", "option");
      btn.setAttribute("aria-selected", String(selectedSet.has(i)));
      if (e.type === "dir") {
        btn.innerHTML = `<div class="fs-tile-thumb fs-folder-glyph" aria-hidden="true"></div>
          <span class="fs-tile-name"></span>`;
      } else {
        const ext = (e.name.match(/\.(\w+)$/)?.[1] || "").toUpperCase();
        btn.innerHTML = `<div class="fs-tile-thumb">
            <img class="fs-thumb" data-src="/fs/thumb?path=${encodeURIComponent(e.path)}" alt="" />
            ${ext ? `<span class="fs-badge fs-tile-badge">${ext}</span>` : ""}
          </div>
          <span class="fs-tile-name"></span>`;
        const img = btn.querySelector(".fs-thumb");
        img.onerror = () => {
          img.style.display = "none";
        };
        obs.observe(img);
      }
      btn.querySelector(".fs-tile-name").textContent = e.name;
      btn.onclick = (ev) => handleClick(ev, i, e.type, e.path);
      btn.ondblclick = () => {
        if (e.type === "file") pick([e.path]);
      };
      gridEl.appendChild(btn);
    });
  }

  function showEmpty() {
    const q = search.value.trim();
    showMsg(q ? c.emptyFiltered || "No matches here." : c.empty || "Nothing to show.");
  }

  function renderView() {
    if (viewMode === "icons") renderGrid();
    else renderDetails();
    updateStatus();
    renderPlaces();
  }

  async function load(dir) {
    selectedSet.clear();
    lastClickIdx = -1;
    paste.value = "";
    try {
      const q = dir ? `?dir=${encodeURIComponent(dir)}` : "";
      const data = await get(`/fs/list${q}`);
      current = data.dir;
      parentDir = data.parent || null;
      pathInput.value = data.dir;
      renderCrumbs(data.dir);
      entries = [];
      if (data.parent) entries.push({ name: `.. (${c.up})`, path: data.parent, type: "dir" });
      for (const e of data.entries) {
        if (filter && e.type === "file" && !filter(e)) continue;
        entries.push(e);
      }
      search.value = "";
      renderView();
    } catch (err) {
      entries = [];
      listEl.innerHTML = "";
      gridEl.innerHTML = "";
      showMsg(`${c.loadError || "Couldn't open this folder."} ${String(err.message || err)}`);
      updateStatus();
    }
  }

  async function goToPath(raw, { pickFile = false } = {}) {
    const path = normalizePastedPath(raw);
    if (!path) return;
    if (!looksLikePath(path)) {
      showMsg(c.badPath || "Enter a full folder or file path.");
      return;
    }
    try {
      const data = await post("/fs/resolve", { path });
      if (data.kind === "dir") {
        await load(data.path);
        return;
      }
      if (data.kind === "file") {
        if (pickFile || !allowDirs) {
          pick([data.path]);
          return;
        }
        paste.value = data.path;
        statusEl.textContent = data.path;
        return;
      }
      showMsg(data.error || c.pathMissing || "Path not found.");
    } catch (err) {
      showMsg(String(err.message || err));
    }
  }

  function onKey(e) {
    if (e.key === "Escape") {
      e.preventDefault();
      return close(true);
    }
    if (e.key === "Enter") {
      if (e.target === paste || e.target === pathInput) return;
      const paths = selectedPaths();
      if (paths.length) {
        e.preventDefault();
        return pick(paths);
      }
      if (looksLikePath(paste.value)) {
        e.preventDefault();
        return goToPath(paste.value, { pickFile: true });
      }
      return;
    }
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const rows = visible();
      if (!rows.length) return;
      const last = selectedSet.size ? Math.max(...selectedSet) : -1;
      const next =
        e.key === "ArrowDown" ? Math.min(rows.length - 1, last + 1) : Math.max(0, last - 1);
      selectedSet.clear();
      selectedSet.add(next);
      lastClickIdx = next;
      renderView();
      (viewMode === "icons" ? gridEl : listEl)
        .querySelector(".selected")
        ?.scrollIntoView({ block: "nearest" });
    }
  }

  function confirmOpen() {
    const paths = selectedPaths();
    if (paths.length) return pick(paths);
    if (looksLikePath(paste.value)) return goToPath(paste.value, { pickFile: !allowDirs });
    if (looksLikePath(pathInput.value) && allowDirs && current) return pick([current]);
    showMsg(c.needSelection || "Select a video, or paste a full file path.");
  }

  revealBtn.onclick = async () => {
    const paths = selectedPaths();
    if (!paths.length) return;
    try {
      await post("/fs/reveal", { path: paths[0] });
    } catch (err) {
      const m = String(err.message || err).toLowerCase();
      if (m.includes("unsupported") || m.includes("404") || m.includes("not found")) {
        revealBtn.hidden = true;
      }
    }
  };

  search.oninput = () => {
    selectedSet.clear();
    lastClickIdx = -1;
    renderView();
  };
  modal.querySelector(".cancel").onclick = () => close(true);
  modal.querySelector(".use-dir")?.addEventListener("click", () => {
    if (current) pick([current]);
  });
  modal.querySelector(".open").onclick = () => confirmOpen();
  upBtn.onclick = () => {
    if (parentDir) load(parentDir);
  };
  modal.querySelector(".fs-path-form").onsubmit = (e) => {
    e.preventDefault();
    goToPath(pathInput.value);
  };
  paste.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      goToPath(paste.value, { pickFile: !allowDirs });
    }
  });

  document.addEventListener("keydown", onKey, true);
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) close(true);
  });

  setViewMode(viewMode);
  (async () => {
    try {
      const data = await get("/fs/places");
      places = data.places || [];
    } catch {
      places = [];
    }
    const preferred =
      startDir ||
      places.find((p) => p.id === "videos")?.path ||
      places.find((p) => p.id === "home")?.path ||
      null;
    await load(preferred);
    search.focus();
  })();
}

export { normalizePastedPath, looksLikePath } from "./fs_path.js";
