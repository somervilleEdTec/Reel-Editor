import { get } from "../api.js";

export function openFileBrowser({ title, filter, startDir, pasteHint, onPick, onCancel }) {
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  const modal = document.createElement("div");
  modal.className = "modal";
  modal.innerHTML = `<h2 class="display" style="font-size:1.25rem">${title}</h2>
    <div class="fs-nav mono"></div>
    <ul class="fs-list"></ul>
    <label class="field">${pasteHint || "Or paste a path"}
      <input class="mono paste" />
    </label>
    <div style="display:flex;gap:.5rem;justify-content:flex-end;margin-top:.75rem;flex-wrap:wrap">
      <button type="button" class="secondary cancel">Cancel</button>
      <button type="button" class="secondary use-dir">Use this folder</button>
      <button type="button" class="open">Open</button>
    </div>`;
  backdrop.appendChild(modal);
  document.body.appendChild(backdrop);

  const list = modal.querySelector(".fs-list");
  const nav = modal.querySelector(".fs-nav");
  const paste = modal.querySelector(".paste");
  let current = startDir || null;

  async function load(dir) {
    const q = dir ? `?dir=${encodeURIComponent(dir)}` : "";
    const data = await get(`/fs/list${q}`);
    current = data.dir;
    nav.textContent = data.dir;
    list.innerHTML = "";
    if (data.parent) {
      const up = document.createElement("li");
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = "↑ Up";
      b.onclick = () => load(data.parent);
      up.appendChild(b);
      list.appendChild(up);
    }
    for (const e of data.entries) {
      if (filter && e.type === "file" && !filter(e)) continue;
      const li = document.createElement("li");
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = (e.type === "dir" ? "📁 " : "") + e.name;
      b.onclick = () => {
        if (e.type === "dir") load(e.path);
        else {
          paste.value = e.path;
        }
      };
      li.appendChild(b);
      list.appendChild(li);
    }
  }

  modal.querySelector(".cancel").onclick = () => {
    backdrop.remove();
    onCancel?.();
  };
  modal.querySelector(".use-dir").onclick = () => {
    if (!current) return;
    backdrop.remove();
    onPick(current);
  };
  modal.querySelector(".open").onclick = () => {
    const path = paste.value.trim();
    if (!path) return;
    backdrop.remove();
    onPick(path);
  };
  load(startDir).catch((err) => {
    nav.textContent = String(err.message || err);
  });
}
