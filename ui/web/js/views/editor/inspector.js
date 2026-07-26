import { mountInspectorAudio } from "./inspector_audio.js";
import { mountInspectorBasics } from "./inspector_basics.js";
import { mountInspectorRank } from "./inspector_rank.js";
import { mountInspectorReframe } from "./inspector_reframe.js";
import { mountInspectorSnapshots } from "./inspector_snapshots.js";
import { mountInspectorTitles } from "./inspector_titles.js";
import { mountInspectorTransitions } from "./inspector_transitions.js";

export function mountInspector(el, { copy, flashSaved }) {
  const rerender = () => mountInspector(el, { copy, flashSaved });
  el.innerHTML = `<div class="ins-basic"></div><div class="ins-audio"></div>
    <div class="ins-transitions"></div><div class="ins-titles"></div>
    <div class="ins-rank"></div><div class="ins-reframe"></div>
    <div class="ins-snapshots"></div>`;
  mountInspectorBasics(el.querySelector(".ins-basic"), { copy, flashSaved, rerender });
  mountInspectorAudio(el.querySelector(".ins-audio"), { copy, flashSaved });
  mountInspectorTransitions(el.querySelector(".ins-transitions"), { copy, flashSaved });
  mountInspectorTitles(el.querySelector(".ins-titles"), { copy, flashSaved, rerender });
  mountInspectorRank(el.querySelector(".ins-rank"), { copy, flashSaved, rerender });
  mountInspectorReframe(el.querySelector(".ins-reframe"), { copy, flashSaved });
  mountInspectorSnapshots(el.querySelector(".ins-snapshots"), { copy, flashSaved, rerender });
}
