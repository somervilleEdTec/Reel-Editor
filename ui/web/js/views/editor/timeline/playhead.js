/**
 * Shared playhead line inside .tl-playhead-layer.
 * Supports drag-to-scrub and programmatic updates.
 */
export function mountPlayhead(layerEl, { zoom, scrollEl, onSeek, getDuration }) {
  const line = document.createElement("div");
  line.className = "tl-playhead-line";
  layerEl.appendChild(line);
  layerEl._ph = { line, zoom };

  let dragging = false;

  line.addEventListener("pointerdown", (e) => {
    e.stopPropagation();
    dragging = true;
    line.setPointerCapture(e.pointerId);
  });

  line.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const canvasLeft = layerEl.getBoundingClientRect().left;
    const x = Math.max(0, e.clientX - canvasLeft);
    const t = Math.min(x / layerEl._ph.zoom, getDuration());
    line.style.left = `${t * layerEl._ph.zoom}px`;
    onSeek(t);
  });

  line.addEventListener("pointerup", () => { dragging = false; });
}

/** Move playhead to output time t (call from store subscription). */
export function updatePlayhead(layerEl, outTime) {
  const ph = layerEl?._ph;
  if (ph) ph.line.style.left = `${outTime * ph.zoom}px`;
}

/** Recalculate all element positions after zoom change. */
export function setPlayheadZoom(layerEl, zoom) {
  if (layerEl?._ph) layerEl._ph.zoom = zoom;
}
