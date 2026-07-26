let _handler = null;

/**
 * Register editor keyboard shortcuts. Call once when the editor mounts.
 * @param {{ getVideo, blade, setTool, undo, redo, zoomIn, zoomOut, fit, trimStart, trimEnd, showHelp, deleteSelected }} actions
 */
export function registerEditorShortcuts(actions) {
  if (_handler) unregisterEditorShortcuts();

  _handler = (e) => {
    const tag = e.target.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
    const ctrl = e.ctrlKey || e.metaKey;

    if (e.code === "Space") {
      e.preventDefault();
      const v = actions.getVideo?.();
      if (v) { if (v.paused) v.play().catch(() => {}); else v.pause(); }
    } else if (e.code === "KeyV" && !ctrl) {
      e.preventDefault();
      actions.setTool?.("select");
    } else if (e.code === "KeyB" && ctrl) {
      e.preventDefault();
      actions.blade?.();
    } else if (e.code === "KeyB" && !ctrl) {
      e.preventDefault();
      actions.setTool?.("blade");
    } else if ((e.key === "Delete" || e.key === "Backspace") && !ctrl) {
      actions.deleteSelected?.();
    } else if (e.key === "[" && !ctrl) {
      e.preventDefault();
      actions.trimStart?.();
    } else if (e.key === "]" && !ctrl) {
      e.preventDefault();
      actions.trimEnd?.();
    } else if (e.code === "KeyZ" && ctrl && e.shiftKey) {
      e.preventDefault();
      actions.redo?.();
    } else if (e.code === "KeyZ" && ctrl) {
      e.preventDefault();
      actions.undo?.();
    } else if ((e.key === "+" || e.key === "=") && !ctrl) {
      actions.zoomIn?.();
    } else if (e.key === "-" && !ctrl) {
      actions.zoomOut?.();
    } else if (e.key === "\\" && !ctrl) {
      actions.fit?.();
    } else if (e.key === "?" && !ctrl) {
      actions.showHelp?.();
    }
  };

  document.addEventListener("keydown", _handler);
}

export function unregisterEditorShortcuts() {
  if (_handler) document.removeEventListener("keydown", _handler);
  _handler = null;
}
