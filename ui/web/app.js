const api = (path, opts) => fetch(path, {
  headers: { "Content-Type": "application/json" },
  ...opts,
}).then(async (r) => {
  if (!r.ok) throw new Error(await r.text());
  return r.json();
});

let project = null;

async function openProject() {
  const path = document.getElementById("path").value;
  project = await api("/project/open", { method: "POST", body: JSON.stringify({ path }) });
  render();
}

function render() {
  const box = document.getElementById("words");
  box.innerHTML = "";
  (project.words || []).forEach((w) => {
    const el = document.createElement("button");
    el.type = "button";
    el.className = "word" + (w.deleted ? " deleted" : "");
    el.textContent = w.text;
    el.title = "Click to toggle delete";
    el.onclick = async () => {
      await api("/words/delete", {
        method: "POST",
        body: JSON.stringify({ word_id: w.id, deleted: !w.deleted }),
      });
      project = await api("/project");
      render();
    };
    box.appendChild(el);
  });
  document.getElementById("bg").value = project.layers.background;
  document.getElementById("preset").value = project.captions.preset;
  const inset = document.getElementById("inset");
  inset.style.left = (project.layers.inset.x * 100) + "%";
  inset.style.top = (project.layers.inset.y * 100) + "%";
  inset.style.width = (project.layers.inset.w * 100) + "%";
  document.getElementById("caption").style.top = (project.captions.y * 100) + "%";
}

document.getElementById("open").onclick = () => openProject().catch(alert);
document.getElementById("export").onclick = async () => {
  try {
    const res = await api("/export", { method: "POST", body: JSON.stringify({}) });
    alert("Exported " + res.out);
  } catch (e) { alert(e.message); }
};
document.getElementById("bg").onchange = async (e) => {
  await api("/layers", { method: "POST", body: JSON.stringify({ background: e.target.value }) });
};
document.getElementById("preset").onchange = async (e) => {
  await api("/captions", { method: "POST", body: JSON.stringify({ preset: e.target.value }) });
};

// Simple inset drag
(() => {
  const el = document.getElementById("inset");
  const stage = document.getElementById("stage");
  let dragging = false;
  el.addEventListener("pointerdown", (e) => { dragging = true; el.setPointerCapture(e.pointerId); });
  el.addEventListener("pointerup", async () => {
    dragging = false;
    if (!project) return;
    const r = stage.getBoundingClientRect();
    const ir = el.getBoundingClientRect();
    const x = (ir.left - r.left) / r.width;
    const y = (ir.top - r.top) / r.height;
    await api("/layers", { method: "POST", body: JSON.stringify({ inset: { x, y } }) });
    project = await api("/project");
  });
  el.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const r = stage.getBoundingClientRect();
    el.style.left = ((e.clientX - r.left) / r.width * 100) + "%";
    el.style.top = ((e.clientY - r.top) / r.height * 100) + "%";
  });
})();
