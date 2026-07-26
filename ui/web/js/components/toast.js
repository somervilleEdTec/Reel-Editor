const host = () => {
  let el = document.querySelector(".toast-host");
  if (!el) {
    el = document.createElement("div");
    el.className = "toast-host";
    document.body.appendChild(el);
  }
  return el;
};

export function toast(message, kind = "ok") {
  const el = document.createElement("div");
  el.className = `toast ${kind === "danger" ? "danger" : ""}`;
  el.textContent = message;
  host().appendChild(el);
  const t = setTimeout(() => el.remove(), 4000);
  el.onmouseenter = () => clearTimeout(t);
}
