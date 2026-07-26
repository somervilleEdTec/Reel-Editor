const INTERVALS = [0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300];
const MIN_PX = 52;

function pickInterval(zoom) {
  return INTERVALS.find((i) => i * zoom >= MIN_PX) ?? 300;
}

function fmt(s) {
  if (s >= 60) return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
  return `${s < 10 ? s.toFixed(1) : Math.floor(s)}s`;
}

export function mountRuler(el, { duration, zoom }) {
  el._dur = duration;
  el._zoom = zoom;
  render(el);
}

export function updateRuler(el, zoom, duration) {
  if (zoom != null) el._zoom = zoom;
  if (duration != null) el._dur = duration;
  render(el);
}

function render(el) {
  el.innerHTML = "";
  const { _dur: dur, _zoom: zoom } = el;
  const step = pickInterval(zoom);
  for (let t = 0; t <= dur + 0.001; t = Math.round((t + step) * 1000) / 1000) {
    const tick = document.createElement("span");
    tick.className = "tl-tick";
    tick.style.left = `${t * zoom}px`;
    tick.textContent = fmt(t);
    el.appendChild(tick);
    if (t >= dur) break;
  }
}
