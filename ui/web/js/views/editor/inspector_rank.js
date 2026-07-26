import { post } from "../../api.js";
import { setState, state } from "../../store.js";
import { formatSeconds, refreshProject, showError } from "./inspector_helpers.js";

export function mountInspectorRank(el, { copy, flashSaved, rerender }) {
  el.innerHTML = `<div class="cluster">
    <p class="section-label">${copy.rank}</p>
    <button type="button" class="secondary run-rank">${copy.runRank}</button>
    <div class="candidate-list"></div>
  </div>`;
  el.querySelector(".run-rank").onclick = () => runRank(el, copy, flashSaved, rerender);
  renderCandidates(el.querySelector(".candidate-list"), copy, flashSaved, rerender);
}

function renderCandidates(el, copy, flashSaved, rerender) {
  const candidates = state.project.candidates || [];
  el.innerHTML = "";
  if (!candidates.length) {
    const empty = document.createElement("p");
    empty.className = "empty-line";
    empty.textContent = copy.noCandidates;
    el.appendChild(empty);
    return;
  }
  candidates.forEach((candidate) => el.appendChild(candidateRow(candidate, copy, flashSaved, rerender)));
}

function candidateRow(candidate, copy, flashSaved, rerender) {
  const row = document.createElement("div");
  row.className = "candidate-row";
  const meta = document.createElement("span");
  meta.textContent = `${candidate.id} - ${formatSeconds(candidate.duration_s)}`;
  const warnings = document.createElement("small");
  warnings.textContent = (candidate.warnings || []).join(", ");
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "secondary";
  btn.textContent = copy.selectCandidate;
  btn.onclick = () => selectCandidate(candidate.id, flashSaved, rerender);
  row.append(meta, warnings, btn);
  return row;
}

async function runRank(root, copy, flashSaved, rerender) {
  const btn = root.querySelector(".run-rank");
  btn.disabled = true;
  try {
    state.project.candidates = (await post("/rank", {})).candidates || [];
    setState({ project: state.project });
    flashSaved();
    renderCandidates(root.querySelector(".candidate-list"), copy, flashSaved, rerender);
  } catch (e) {
    showError(e);
  } finally {
    btn.disabled = false;
  }
}

async function selectCandidate(candidate_id, flashSaved, rerender) {
  try {
    await post("/select", { candidate_id });
    await refreshProject(flashSaved);
    rerender();
  } catch (e) {
    showError(e);
  }
}
