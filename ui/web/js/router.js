import { get } from "./api.js";
import { setState, state } from "./store.js";
import { renderSetup } from "./views/setup.js";
import { renderHome } from "./views/home.js";
import { renderEditor } from "./views/editor/index.js";

const routes = {
  setup: renderSetup,
  home: renderHome,
  editor: renderEditor,
};

export function route() {
  const hash = (location.hash || "#/").replace(/^#\/?/, "");
  const name = hash.split("?")[0] || "home";
  return name in routes ? name : "home";
}

export async function boot() {
  const app = document.getElementById("app");
  const [copy, setup] = await Promise.all([
    get("/content/copy.json"),
    get("/setup/status"),
  ]);
  setState({ copy, setup });
  let target = route();
  if (!setup.complete && !setup.completed) target = "setup";
  else if (target === "setup" && (setup.complete || setup.completed)) target = "home";
  else if (target === "editor") {
    try {
      const project = await get("/project");
      setState({ project });
    } catch {
      target = "home";
    }
  }
  navigate(target, true);
  window.addEventListener("hashchange", () => navigate(route()));
}

export function navigate(name, replace = false) {
  const next = `#/${name}`;
  if (replace) history.replaceState(null, "", next);
  else if (location.hash !== next) {
    location.hash = next; // hashchange handler re-enters navigate and renders once
    return;
  }
  const app = document.getElementById("app");
  document.body.classList.toggle("branded", name === "setup" || name === "home");
  document.body.classList.toggle("editor-chrome", name === "editor");
  const render = routes[name] || routes.home;
  render(app, state);
}
