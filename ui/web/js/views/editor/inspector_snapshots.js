import { get, post } from "../../api.js";
import { setState } from "../../store.js";
import { showError } from "./inspector_helpers.js";

export function mountInspectorSnapshots(el, { copy, flashSaved, rerender }) {
  el.innerHTML = `<div class="cluster">
    <p class="section-label">${copy.snapshots}</p>
    <div class="snapshot-save">
      <input class="snapshot-name" placeholder="${copy.snapshotName}" />
      <button type="button" class="secondary save-snapshot">${copy.saveSnapshot}</button>
    </div>
    <div class="snapshot-list"></div>
  </div>`;
  el.querySelector(".save-snapshot").onclick = () => saveSnapshot(el, copy, flashSaved, rerender);
  loadSnapshots(el, copy, flashSaved, rerender);
}

async function loadSnapshots(root, copy, flashSaved, rerender) {
  const list = root.querySelector(".snapshot-list");
  try {
    const snapshots = (await get("/project/snapshots")).snapshots || [];
    list.innerHTML = "";
    if (!snapshots.length) {
      const empty = document.createElement("p");
      empty.className = "empty-line";
      empty.textContent = copy.noSnapshots;
      list.appendChild(empty);
      return;
    }
    snapshots.forEach((snapshot) => {
      list.appendChild(snapshotRow(snapshot, copy, flashSaved, rerender));
    });
  } catch (e) {
    showError(e);
  }
}

function snapshotRow(snapshot, copy, flashSaved, rerender) {
  const row = document.createElement("div");
  row.className = "snapshot-row";
  const label = document.createElement("span");
  label.textContent = snapshot.name;
  const date = document.createElement("small");
  date.textContent = new Date(snapshot.created_at).toLocaleString();
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "secondary";
  btn.textContent = copy.restoreSnapshot;
  btn.onclick = () => restoreSnapshot(snapshot.name, flashSaved, rerender);
  row.append(label, date, btn);
  return row;
}

async function saveSnapshot(root, copy, flashSaved, rerender) {
  const name = root.querySelector(".snapshot-name").value.trim();
  try {
    await post("/project/snapshots", { name });
    flashSaved();
    await loadSnapshots(root, copy, flashSaved, rerender);
  } catch (e) {
    showError(e);
  }
}

async function restoreSnapshot(name, flashSaved, rerender) {
  try {
    setState({ project: await post("/project/snapshots/restore", { name }) });
    flashSaved();
    rerender();
  } catch (e) {
    showError(e);
  }
}
