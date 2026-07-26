import { get, post } from "../api.js";
import { state } from "../store.js";

/**
 * Modal file/folder browser: breadcrumbs, search, keyboard, large-icons / details view,
 * multi-select (Ctrl/Cmd, Shift-range), Reveal in Explorer.
 *
 * Callbacks:
 *   onPick(path)           — single path, backward-compat
 *   onPickMany(paths[])    — preferred; called with array of selected paths
 * Both are optional; if onPickMany is set it takes priority.
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
    <nav class="fs-crumbs" aria-label="Path"></nav>
    <input class="fs-search" type="search" placeholder="${c.search || "Search this folder"}" />
    <ul class="fs-list" role="listbox" hidden></ul>
    <div class="fs-grid" role="listbox" hidden></div>
    <div class="fs-msg" hidden></div>
    <label class="field">${pasteHint || c.paste}
      <input class="mono paste" />
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
  const msg = modal.querySelector(".fs-msg");
  const search = modal.querySelector(".fs-search");
  const paste = modal.querySelector(".paste");
  const revealBtn = modal.querySelector(".reveal");

  let current = startDir || null;
  let entries = [];
  let selectedSet = new Set();
  let lastClickIdx = -1;
  let viewMode = defaultView || "icons";

  // ── view toggle ──────────────────────────────────────────────────────────
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

  // ── close / pick ─────────────────────────────────────────────────────────
  function close(cancelled) {
    backdrop.remove();
    document.removeEventListener("keydown", onKey, true);
    if (cancelled) onCancel?.();
  }

  function pick(paths) {
    backdrop.remove();
    document.removeEventListener("keydown", onKey, true);
    const arr = Array.isArray(paths) ? paths.filter(Boolean) : [paths].filter(Boolean);
    if (!arr.length) return;
    if (onPickMany) onPickMany(arr);
    else if (onPick) onPick(arr[0]);
  }

  // ── selection helpers ────────────────────────────────────────────────────
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

  function updatePaste() {
    const paths = selectedPaths();
    if (paths.length === 1) paste.value = paths[0];
    else if (paths.length > 1) paste.value = `${paths.length} ${c.selectedCount || "selected"}`;
    else paste.value = "";
  }

  function handleClick(ev, idx, type, path) {
    if (type === "dir") { load(path); return; }
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
    updatePaste();
    renderView();
  }

  // ── breadcrumbs ──────────────────────────────────────────────────────────
  function renderCrumbs(dir) {
    crumbs.innerHTML = "";
    const sep = dir.includes("\\") ? "\\" : "/";
    const parts = dir.split(/[\\/]/).filter(Boolean);
    let acc = dir.startsWith("/") ? "" : null;
    const frag = document.createDocumentFragment();
    const addCrumb = (label, target, isLast) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "fs-crumb"; b.textContent = label;
      if (isLast) b.setAttribute("aria-current", "true");
      b.onclick = () => load(target);
      frag.appendChild(b);
      if (!isLast) {
        const s = document.createElement("span");
        s.className = "fs-crumb-sep"; s.textContent = "›"; frag.appendChild(s);
      }
    };
    if (acc === "") addCrumb(sep, sep, parts.length === 0);
    parts.forEach((part, i) => {
      acc = acc === null ? part : `${acc}${sep}${part}`;
      addCrumb(part, acc + (i === 0 && part.endsWith(":") ? sep : ""), i === parts.length - 1);
    });
    crumbs.appendChild(frag);
  }

  // ── details (list) render ────────────────────────────────────────────────
  function renderDetails() {
    const rows = visible();
    listEl.innerHTML = "";
    msg.hidden = true;
    if (!rows.length) { showEmpty(); return; }
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
      b.ondblclick = () => { if (e.type === "file") pick([e.path]); };
      li.appendChild(b);
      listEl.appendChild(li);
    });
  }

  // ── large icons (grid) render ────────────────────────────────────────────
  let thumbObserver = null;
  function getObserver() {
    if (!thumbObserver) {
      thumbObserver = new IntersectionObserver((ents) => {
        ents.forEach((en) => {
          if (en.isIntersecting) {
            const img = en.target;
            img.src = img.dataset.src;
            thumbObserver.unobserve(img);
          }
        });
      }, { rootMargin: "120px" });
    }
    return thumbObserver;
  }

  function renderGrid() {
    const rows = visible();
    gridEl.innerHTML = "";
    msg.hidden = true;
    if (!rows.length) { showEmpty(); return; }
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
        img.onerror = () => { img.style.display = "none"; };
        obs.observe(img);
      }
      btn.querySelector(".fs-tile-name").textContent = e.name;
      btn.onclick = (ev) => handleClick(ev, i, e.type, e.path);
      btn.ondblclick = () => { if (e.type === "file") pick([e.path]); };
      gridEl.appendChild(btn);
    });
  }

  function showEmpty() {
    const q = search.value.trim();
    msg.hidden = false;
    msg.textContent = q ? c.emptyFiltered || "No matches here." : c.empty || "Nothing to show.";
  }

  function renderView() {
    if (viewMode === "icons") { renderGrid(); }
    else { renderDetails(); }
    revealBtn.hidden = selectedPaths().length !== 1;
  }

  // ── load directory ───────────────────────────────────────────────────────
  async function load(dir) {
    selectedSet.clear();
    lastClickIdx = -1;
    try {
      const q = dir ? `?dir=${encodeURIComponent(dir)}` : "";
      const data = await get(`/fs/list${q}`);
      current = data.dir;
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
      msg.hidden = false;
      msg.textContent = `${c.loadError || "Couldn't open this folder."} ${String(err.message || err)}`;
    }
  }

  // ── keyboard ─────────────────────────────────────────────────────────────
  function onKey(e) {
    if (e.key === "Escape") { e.preventDefault(); return close(true); }
    if (e.key === "Enter") {
      if (e.target === paste) { e.preventDefault(); return confirmOpen(); }
      const paths = selectedPaths();
      if (paths.length) { e.preventDefault(); return pick(paths); }
      if (paste.value.trim()) { e.preventDefault(); return confirmOpen(); }
      return;
    }
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const rows = visible();
      if (!rows.length) return;
      const last = selectedSet.size ? Math.max(...selectedSet) : -1;
      const next = e.key === "ArrowDown"
        ? Math.min(rows.length - 1, last + 1)
        : Math.max(0, last - 1);
      selectedSet.clear(); selectedSet.add(next); lastClickIdx = next;
      if (rows[next]?.type === "file") paste.value = rows[next].path;
      renderView();
      (viewMode === "icons" ? gridEl : listEl)
        .querySelector(".selected")?.scrollIntoView({ block: "nearest" });
    }
  }

  function confirmOpen() {
    const path = normalizePastedPath(paste.value);
    if (!path) return;
    pick([path]);
  }

  // ── reveal ───────────────────────────────────────────────────────────────
  revealBtn.onclick = async () => {
    const paths = selectedPaths();
    if (!paths.length) return;
    try {
      await post("/fs/reveal", { path: paths[0] });
    } catch (err) {
      const msg = String(err.message || err).toLowerCase();
      if (msg.includes("unsupported") || msg.includes("404") || msg.includes("not found")) {
        revealBtn.hidden = true;
      }
    }
  };

  // ── wire events ──────────────────────────────────────────────────────────
  search.oninput = () => { selectedSet.clear(); lastClickIdx = -1; renderView(); };
  modal.querySelector(".cancel").onclick = () => close(true);
  modal.querySelector(".use-dir")?.addEventListener("click", () => { if (current) pick([current]); });
  modal.querySelector(".open").onclick = () => {
    const paths = selectedPaths();
    if (paths.length) return pick(paths);
    confirmOpen();
  };
  document.addEventListener("keydown", onKey, true);
  backdrop.addEventListener("click", (e) => { if (e.target === backdrop) close(true); });

  setViewMode(viewMode);
  load(startDir).then(() => search.focus());
}

// ── helpers ───────────────────────────────────────────────────────────────

function fmtSize(n) {
  if (n < 1024) return `${n} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let v = n; let i = -1;
  do { v /= 1024; i += 1; } while (v >= 1024 && i < units.length - 1);
  return `${v >= 10 ? Math.round(v) : v.toFixed(1)} ${units[i]}`;
}

/** Strip Explorer "Copy as path" quotes, BOM, and file:// wrappers. */
export function normalizePastedPath(raw) {
  let s = String(raw || "").trim().replace(/^\uFEFF/, "").trim();
  if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) {
    s = s.slice(1, -1).trim();
  }
  if (/^file:/i.test(s)) {
    try {
      const u = new URL(s);
      s = decodeURIComponent(u.pathname || "");
      if (/^\/[A-Za-z]:\//.test(s)) s = s.slice(1);
    } catch { /* keep s */ }
  }
  return s;
}
