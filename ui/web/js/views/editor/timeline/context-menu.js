let _menu = null;

export function showContextMenu(x, y, items) {
  dismissContextMenu();
  const menu = document.createElement("div");
  menu.className = "tl-menu";
  menu.style.left = `${x}px`;
  menu.style.top = `${y}px`;
  items.forEach(({ label, action, disabled }) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = label;
    btn.disabled = !!disabled;
    btn.onclick = () => {
      dismissContextMenu();
      action?.();
    };
    menu.appendChild(btn);
  });
  document.body.appendChild(menu);
  _menu = menu;
  const close = (e) => {
    if (_menu && !menu.contains(e.target)) dismissContextMenu();
  };
  setTimeout(() => {
    document.addEventListener("pointerdown", close, { once: true });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") dismissContextMenu();
    }, { once: true });
  }, 0);
}

export function dismissContextMenu() {
  if (_menu) {
    _menu.remove();
    _menu = null;
  }
}
