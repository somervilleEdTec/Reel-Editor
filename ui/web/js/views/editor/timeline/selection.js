/** Shared timeline selection state (A-roll seg/gap, B-roll clip, range). */
let _sel = { kind: null, data: null };

export function getSelection() {
  return _sel;
}

export function setSelection(kind, data, roots = {}) {
  _sel = { kind, data };
  clearVisual(roots);
  if (kind === "seg" && data?.el) data.el.classList.add("selected");
  if (kind === "gap" && data?.el) data.el.classList.add("selected");
  if (kind === "clip" && data?.el) data.el.classList.add("selected");
  if (kind === "range" && data?.el) data.el.classList.add("selected");
  document.dispatchEvent(new CustomEvent("tl-selection", { detail: _sel }));
}

export function clearSelection(roots = {}) {
  _sel = { kind: null, data: null };
  clearVisual(roots);
  document.dispatchEvent(new CustomEvent("tl-selection", { detail: _sel }));
}

function clearVisual(roots) {
  const scopes = [roots.edlEl, roots.brollEl, roots.canvas].filter(Boolean);
  if (!scopes.length) {
    document.querySelectorAll(".tl-seg.selected, .tl-gap.selected, .tl-clip.selected, .tl-range")
      .forEach((n) => { n.classList.remove("selected"); if (n.classList.contains("tl-range")) n.remove(); });
    return;
  }
  scopes.forEach((root) => {
    root.querySelectorAll(".tl-seg.selected, .tl-gap.selected, .tl-clip.selected")
      .forEach((n) => n.classList.remove("selected"));
    root.querySelectorAll(".tl-range").forEach((n) => n.remove());
  });
}
