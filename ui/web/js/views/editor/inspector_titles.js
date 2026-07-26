import { post } from "../../api.js";
import { setState, state } from "../../store.js";
import { showError } from "./inspector_helpers.js";

export function mountInspectorTitles(el, { copy, flashSaved, rerender }) {
  el.innerHTML = `<div class="cluster">
    <p class="section-label">${copy.titles}</p>
    <div class="title-add">
      <input class="new-title-text" placeholder="${copy.titleText}" />
      <div class="compact-grid">
        <label class="field">${copy.titleStart}<input type="number" class="new-title-start" min="0" step="0.1" value="0" /></label>
        <label class="field">${copy.titleEnd}<input type="number" class="new-title-end" min="0" step="0.1" value="5" /></label>
      </div>
      <button type="button" class="secondary add-title">${copy.addTitle}</button>
    </div>
    <div class="title-list"></div>
  </div>`;
  renderList(el.querySelector(".title-list"), copy, flashSaved, rerender);
  el.querySelector(".add-title").onclick = () => addTitle(el, flashSaved, rerender);
}

function renderList(el, copy, flashSaved, rerender) {
  const titles = state.project.titles || [];
  el.innerHTML = "";
  if (!titles.length) {
    const empty = document.createElement("p");
    empty.className = "empty-line";
    empty.textContent = copy.noTitles;
    el.appendChild(empty);
    return;
  }
  titles.forEach((title) => el.appendChild(titleRow(title, copy, flashSaved, rerender)));
}

function titleRow(title, copy, flashSaved, rerender) {
  const row = document.createElement("div");
  row.className = "title-row";
  row.dataset.id = title.id;
  const text = input("text", "title-text", title.text);
  const start = input("number", "title-start", title.start_out_s, "0.1");
  const end = input("number", "title-end", title.end_out_s, "0.1");
  const y = input("number", "title-y", title.y ?? 0.5, "0.05");
  row.append(
    field(copy.titleText, text),
    compact(field(copy.titleStart, start), field(copy.titleEnd, end), field(copy.titleY, y)),
    removeButton(copy.removeTitle, title.id, flashSaved, rerender),
  );
  text.onchange = () => saveTitle(title.id, { text: text.value }, flashSaved, rerender);
  start.onchange = () => saveTitle(title.id, { start_out_s: Number(start.value) }, flashSaved, rerender);
  end.onchange = () => saveTitle(title.id, { end_out_s: Number(end.value) }, flashSaved, rerender);
  y.onchange = () => saveTitle(title.id, { y: Number(y.value) }, flashSaved, rerender);
  return row;
}

function input(type, className, value, step) {
  const el = document.createElement("input");
  el.type = type;
  el.className = className;
  if (type === "number") {
    el.min = "0";
    if (step) el.step = step;
  }
  el.value = value ?? "";
  return el;
}

function field(label, control) {
  const wrap = document.createElement("label");
  wrap.className = "field";
  wrap.append(label, control);
  return wrap;
}

function compact(...children) {
  const wrap = document.createElement("div");
  wrap.className = "compact-grid";
  wrap.append(...children);
  return wrap;
}

function removeButton(label, id, flashSaved, rerender) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "secondary";
  btn.textContent = label;
  btn.onclick = () => saveTitle(id, { deleted: true }, flashSaved, rerender);
  return btn;
}

async function addTitle(root, flashSaved, rerender) {
  const text = root.querySelector(".new-title-text").value.trim();
  const start = Number(root.querySelector(".new-title-start").value);
  const end = Number(root.querySelector(".new-title-end").value);
  await saveTitle(null, { text, start_out_s: start, end_out_s: end }, flashSaved, rerender);
}

async function saveTitle(id, patch, flashSaved, rerender) {
  try {
    const body = id ? { id, ...patch } : patch;
    state.project.titles = (await post("/titles", body)).titles || [];
    setState({ project: state.project });
    flashSaved();
    rerender();
  } catch (e) {
    showError(e);
  }
}
