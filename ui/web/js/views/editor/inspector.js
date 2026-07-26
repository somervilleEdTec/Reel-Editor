import { mountInspectorAudio } from "./inspector_audio.js";
import { mountInspectorBasics } from "./inspector_basics.js";
import { mountInspectorRank } from "./inspector_rank.js";
import { mountInspectorReframe } from "./inspector_reframe.js";
import { mountInspectorSnapshots } from "./inspector_snapshots.js";
import { mountInspectorTitles } from "./inspector_titles.js";
import { mountInspectorTransitions } from "./inspector_transitions.js";

const SECTIONS = [
  { key: "basic", label: "Basics", mount: mountInspectorBasics, rerender: true },
  { key: "audio", labelKey: "audio", mount: mountInspectorAudio },
  { key: "transitions", labelKey: "transitions", mount: mountInspectorTransitions },
  { key: "titles", labelKey: "titles", mount: mountInspectorTitles, rerender: true },
  { key: "rank", labelKey: "rank", mount: mountInspectorRank, rerender: true },
  { key: "reframe", labelKey: "tools", mount: mountInspectorReframe },
  { key: "snapshots", labelKey: "snapshots", mount: mountInspectorSnapshots, rerender: true },
];

export function mountInspector(el, { copy, flashSaved }) {
  const rerender = () => mountInspector(el, { copy, flashSaved });
  const openKeys = new Set(
    [...el.querySelectorAll(".ins-section.open")].map((n) => n.dataset.key),
  );
  if (!openKeys.size) openKeys.add("basic");

  el.innerHTML = SECTIONS.map((s) => {
    const label = s.label || copy[s.labelKey] || s.key;
    const open = openKeys.has(s.key);
    return `<div class="ins-section${open ? " open" : ""}" data-key="${s.key}">
      <button type="button" class="ins-toggle" aria-expanded="${open}">${label}</button>
      <div class="ins-body ins-${s.key}"></div>
    </div>`;
  }).join("");

  el.querySelectorAll(".ins-toggle").forEach((btn) => {
    btn.onclick = () => {
      const section = btn.closest(".ins-section");
      const willOpen = !section.classList.contains("open");
      section.classList.toggle("open", willOpen);
      btn.setAttribute("aria-expanded", String(willOpen));
    };
  });

  SECTIONS.forEach((s) => {
    const body = el.querySelector(`.ins-${s.key}`);
    s.mount(body, { copy, flashSaved, ...(s.rerender ? { rerender } : {}) });
  });
}
