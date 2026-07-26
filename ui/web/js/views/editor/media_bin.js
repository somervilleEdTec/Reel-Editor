import { post } from "../../api.js";
import { state, setState } from "../../store.js";
import { toast } from "../../components/toast.js";
import { openFileBrowser } from "../../components/filebrowser.js";

/** Compact grid of project sources with add / remove actions. */
export function mountMediaBin(el, { copy, flashSaved }) {
  render();

  function render() {
    const sources = state.project?.sources || [];
    el.innerHTML = "";

    if (!sources.length) {
      const empty = document.createElement("p");
      empty.className = "mb-empty";
      empty.textContent = copy.emptyMedia;
      el.appendChild(empty);
    } else {
      const grid = document.createElement("div");
      grid.className = "mb-grid";
      sources.forEach((src, i) => {
        grid.appendChild(makeTile(src, i));
      });
      el.appendChild(grid);
    }

    const actions = document.createElement("div");
    actions.className = "mb-actions";
    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.textContent = copy.addMedia;
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "secondary";
    removeBtn.textContent = copy.removeMedia;
    actions.appendChild(addBtn);
    actions.appendChild(removeBtn);
    el.appendChild(actions);

    addBtn.onclick = addSources;
    removeBtn.onclick = removeSources;
  }

  function makeTile(src, idx) {
    const tile = document.createElement("div");
    tile.className = "mb-tile";
    tile.dataset.idx = idx;
    const thumbSrc = src.path
      ? `/fs/thumb?path=${encodeURIComponent(src.path)}`
      : `/media/source?id=${encodeURIComponent(src.id || "")}`;
    const label = src.name || (src.path ? src.path.split(/[/\\]/).pop() : src.id || "");
    tile.innerHTML = `<div class="mb-thumb-wrap">
        <img class="mb-thumb" src="${thumbSrc}" alt="" loading="lazy" />
        ${src.role ? `<span class="mb-role">${src.role}</span>` : ""}
        ${src.duration != null ? `<span class="mb-dur">${fmtDuration(src.duration)}</span>` : ""}
      </div>
      <span class="mb-name"></span>`;
    tile.querySelector(".mb-thumb").onerror = function () { this.style.display = "none"; };
    tile.querySelector(".mb-name").textContent = label;
    tile.onclick = (ev) => {
      if (ev.ctrlKey || ev.metaKey) {
        tile.classList.toggle("selected");
      } else {
        el.querySelectorAll(".mb-tile.selected").forEach((t) => {
          if (t !== tile) t.classList.remove("selected");
        });
        tile.classList.toggle("selected");
      }
    };
    return tile;
  }

  function addSources() {
    openFileBrowser({
      title: copy.addMedia,
      defaultView: "icons",
      filter: (e) => /\.(mp4|mov|mkv|webm|avi|m4v|mxf|mp3|wav|m4a|aac|flac)$/i.test(e.name),
      onPickMany: async (paths) => {
        for (const path of paths) {
          try {
            const updated = await post("/sources/add", { path });
            if (updated) setState({ project: updated });
          } catch (err) {
            toast(String(err.message || err), "danger");
          }
        }
        flashSaved();
        render();
      },
      onPick: async (path) => {
        try {
          const updated = await post("/sources/add", { path });
          if (updated) setState({ project: updated });
          flashSaved();
          render();
        } catch (err) {
          toast(String(err.message || err), "danger");
        }
      },
      onCancel: () => {},
    });
  }

  async function removeSources() {
    const selected = [...el.querySelectorAll(".mb-tile.selected")];
    if (!selected.length) return;
    const { project } = state;
    const sources = project?.sources || [];
    const clips = project?.assembly?.clips || [];
    const toRemove = selected.map((t) => sources[+t.dataset.idx]).filter(Boolean);
    const usedNames = toRemove
      .filter((src) => clips.some((cl) => cl.source_id === src.id))
      .map((s) => s.name || s.id);
    const warn = usedNames.length ? ` ${copy.removeUsedWarn}` : "";
    if (!confirm(`${copy.removeConfirm} ${toRemove.length > 1 ? `${toRemove.length} sources` : (toRemove[0]?.name || "")}?${warn}`)) return;
    for (const src of toRemove) {
      try {
        const updated = await post("/sources/remove", { id: src.id });
        if (updated) setState({ project: updated });
      } catch (err) {
        toast(String(err.message || err), "danger");
      }
    }
    flashSaved();
    render();
  }
}

function fmtDuration(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}
