import { get } from "../api.js";
import { state } from "../store.js";

/** Modal file/folder browser: breadcrumbs, search, keyboard, type badges. */
export function openFileBrowser({
  title,
  filter,
  startDir,
  pasteHint,
  onPick,
  onCancel,
  allowDirs = false,
}) {
  const c = { ...(state.copy?.filebrowser || {}) };
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  const modal = document.createElement("div");
  modal.className = "modal fs-modal";
  modal.setAttribute("role", "dialog");
  modal.setAttribute("aria-modal", "true");
  modal.innerHTML = `<h2 class="display" style="font-size:1.25rem">${title || c.title}</h2>
    <p class="fs-hint">${allowDirs ? c.hintFolder || "" : c.hintFile || ""}</p>
    <nav class="fs-crumbs" aria-label="Path"></nav>
    <input class="fs-search" type="search" placeholder="${c.search || "Search this folder"}" />
    <ul class="fs-list" role="listbox"></ul>
    <div class="fs-msg" hidden></div>
    <label class="field">${pasteHint || c.paste}
      <input class="mono paste" />
    </label>
    <div class="fs-actions">
      <button type="button" class="secondary cancel">${c.cancel}</button>
      ${allowDirs ? `<button type="button" class="use-dir">${c.useFolder || "Use this folder"}</button>` : ""}
      <button type="button" class="${allowDirs ? "secondary" : ""} open">${c.open}</button>
    </div>`;
  backdrop.appendChild(modal);
  document.body.appendChild(backdrop);

  const list = modal.querySelector(".fs-list");
  const crumbs = modal.querySelector(".fs-crumbs");
  const msg = modal.querySelector(".fs-msg");
  const search = modal.querySelector(".fs-search");
  const paste = modal.querySelector(".paste");
  let current = startDir || null;
  let entries = [];
  let selected = -1;

  function close(cancelled) {
    backdrop.remove();
    document.removeEventListener("keydown", onKey, true);
    if (cancelled) onCancel?.();
  }
  function pick(path) {
    backdrop.remove();
    document.removeEventListener("keydown", onKey, true);
    onPick(path);
  }

  function renderCrumbs(dir) {
    crumbs.innerHTML = "";
    const sep = dir.includes("\\") ? "\\" : "/";
    const parts = dir.split(/[\\/]/).filter(Boolean);
    let acc = dir.startsWith("/") ? "" : null;
    const frag = document.createDocumentFragment();
    const addCrumb = (label, target, isLast) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "fs-crumb";
      b.textContent = label;
      if (isLast) b.setAttribute("aria-current", "true");
      b.onclick = () => load(target);
      frag.appendChild(b);
      if (!isLast) {
        const s = document.createElement("span");
        s.className = "fs-crumb-sep";
        s.textContent = "›";
        frag.appendChild(s);
      }
    };
    if (acc === "") addCrumb(sep, sep, parts.length === 0);
    parts.forEach((part, i) => {
      acc = acc === null ? part : `${acc}${sep}${part}`;
      const target = acc + (i === 0 && part.endsWith(":") ? sep : "");
      addCrumb(part, target, i === parts.length - 1);
    });
    crumbs.appendChild(frag);
  }

  function renderList() {
    const q = search.value.trim().toLowerCase();
    list.innerHTML = "";
    msg.hidden = true;
    const visible = entries.filter((e) => !q || e.name.toLowerCase().includes(q));
    if (!visible.length) {
      msg.hidden = false;
      msg.textContent = q ? c.emptyFiltered || "No matches here." : c.empty || "Nothing to show in this folder.";
      return;
    }
    visible.forEach((e, i) => {
      const li = document.createElement("li");
      const b = document.createElement("button");
      b.type = "button";
      b.className = `fs-row ${e.type === "dir" ? "fs-dir" : "fs-file"}${i === selected ? " selected" : ""}`;
      b.setAttribute("role", "option");
      const ext = e.type === "file" ? (e.name.match(/\.(\w+)$/)?.[1] || "").toUpperCase() : "";
      const size = e.type === "file" && e.size != null ? fmtSize(e.size) : "";
      b.innerHTML = `<span class="fs-icon" aria-hidden="true"></span>
        <span class="fs-name"></span>
        ${size ? `<span class="fs-size">${size}</span>` : ""}
        ${ext ? `<span class="fs-badge">${ext}</span>` : ""}`;
      b.querySelector(".fs-name").textContent = e.name;
      b.onclick = () => {
        if (e.type === "dir") return load(e.path);
        selected = i;
        paste.value = e.path;
        renderList();
      };
      b.ondblclick = () => {
        if (e.type === "file") pick(e.path);
      };
      li.appendChild(b);
      list.appendChild(li);
    });
  }

  async function load(dir) {
    selected = -1;
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
      renderList();
    } catch (err) {
      entries = [];
      list.innerHTML = "";
      msg.hidden = false;
      msg.textContent = `${c.loadError || "Couldn't open this folder."} ${String(err.message || err)}`;
    }
  }

  function visibleRows() {
    const q = search.value.trim().toLowerCase();
    return entries.filter((e) => !q || e.name.toLowerCase().includes(q));
  }

  function onKey(e) {
    if (e.key === "Escape") {
      e.preventDefault();
      return close(true);
    }
    if (e.key === "Enter") {
      if (e.target === paste) {
        e.preventDefault();
        return confirmOpen();
      }
      const rows = visibleRows();
      const sel = rows[selected];
      if (sel) {
        e.preventDefault();
        return sel.type === "dir" ? load(sel.path) : pick(sel.path);
      }
      if (paste.value.trim()) {
        e.preventDefault();
        return confirmOpen();
      }
      return;
    }
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const rows = visibleRows();
      if (!rows.length) return;
      selected = e.key === "ArrowDown"
        ? Math.min(rows.length - 1, selected + 1)
        : Math.max(0, selected - 1);
      const sel = rows[selected];
      if (sel?.type === "file") paste.value = sel.path;
      renderList();
      list.querySelector(".fs-row.selected")?.scrollIntoView({ block: "nearest" });
    }
  }

  function confirmOpen() {
    const path = normalizePastedPath(paste.value);
    if (!path) return;
    pick(path);
  }

  search.oninput = () => {
    selected = -1;
    renderList();
  };
  modal.querySelector(".cancel").onclick = () => close(true);
  modal.querySelector(".use-dir")?.addEventListener("click", () => {
    if (current) pick(current);
  });
  modal.querySelector(".open").onclick = confirmOpen;
  document.addEventListener("keydown", onKey, true);
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) close(true);
  });
  load(startDir).then(() => search.focus());
}

function fmtSize(n) {
  if (n < 1024) return `${n} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let v = n;
  let i = -1;
  do { v /= 1024; i += 1; } while (v >= 1024 && i < units.length - 1);
  return `${v >= 10 ? Math.round(v) : v.toFixed(1)} ${units[i]}`;
}

/** Strip Explorer "Copy as path" quotes, BOM, and file:// wrappers. */
export function normalizePastedPath(raw) {
  let s = String(raw || "").trim().replace(/^\uFEFF/, "").trim();
  if (
    (s.startsWith('"') && s.endsWith('"')) ||
    (s.startsWith("'") && s.endsWith("'"))
  ) {
    s = s.slice(1, -1).trim();
  }
  if (/^file:/i.test(s)) {
    try {
      const u = new URL(s);
      s = decodeURIComponent(u.pathname || "");
      if (/^\/[A-Za-z]:\//.test(s)) s = s.slice(1);
    } catch {
      /* keep s */
    }
  }
  return s;
}
