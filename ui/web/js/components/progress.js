export function progressBar(pct, running = false) {
  const wrap = document.createElement("div");
  wrap.className = `progress${running ? " running" : ""}`;
  const bar = document.createElement("span");
  bar.style.width = `${Math.max(0, Math.min(100, pct * 100))}%`;
  wrap.appendChild(bar);
  return wrap;
}

export function setProgress(el, pct, running) {
  el.classList.toggle("running", !!running);
  const bar = el.querySelector("span");
  if (bar) bar.style.width = `${Math.max(0, Math.min(100, pct * 100))}%`;
}
