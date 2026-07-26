export function openSheet(title, bodyEl, { onClose } = {}) {
  const backdrop = document.createElement("div");
  backdrop.className = "sheet-backdrop";
  const sheet = document.createElement("div");
  sheet.className = "sheet";
  const h = document.createElement("h2");
  h.className = "display";
  h.style.fontSize = "1.35rem";
  h.textContent = title;
  sheet.appendChild(h);
  sheet.appendChild(bodyEl);
  backdrop.appendChild(sheet);
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) {
      backdrop.remove();
      onClose?.();
    }
  });
  document.body.appendChild(backdrop);
  return {
    el: backdrop,
    close() {
      backdrop.remove();
      onClose?.();
    },
  };
}
