import { get, post } from "../../api.js";
import { state, setState } from "../../store.js";
import { toast } from "../../components/toast.js";
import { progressBar, setProgress } from "../../components/progress.js";

export function mountTranscript(el, { copy, flashSaved }) {
  render();

  async function render() {
    const project = state.project;
    const words = project?.words || [];
    const removed = words.filter((w) => w.deleted).length;
    el.innerHTML = `<div class="rail-head">
        <span class="section-label">${copy.transcript}</span>
        ${removed ? `<span class="count-chip">${removed} ${copy.removed}</span>` : ""}
      </div>
      <input class="find" placeholder="${copy.find}" />
      <div class="words" tabindex="0" role="listbox"></div>
      <div class="empty" hidden></div>`;

    const box = el.querySelector(".words");
    const empty = el.querySelector(".empty");
    if (!words.length) {
      box.hidden = true;
      empty.hidden = false;
      empty.innerHTML = `<p>${copy.noWords}</p><button type="button" class="transcribe">${copy.transcribe}</button>
        <div class="tprog" hidden></div>`;
      empty.querySelector(".transcribe").onclick = runTranscribe;
      return;
    }
    box.hidden = false;
    empty.hidden = true;
    let focus = 0;
    words.forEach((w, i) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `chip${w.deleted ? " deleted" : ""}`;
      btn.textContent = w.text;
      btn.role = "option";
      btn.onclick = () => toggle(w, btn);
      box.appendChild(btn);
    });
    el.querySelector(".find").oninput = (e) => {
      const q = e.target.value.toLowerCase();
      [...box.children].forEach((ch, i) => {
        ch.hidden = q && !words[i].text.toLowerCase().includes(q);
      });
    };
    box.onkeydown = (e) => {
      const kids = [...box.querySelectorAll(".chip:not([hidden])")];
      if (!kids.length) return;
      if (e.key === "ArrowRight") {
        focus = Math.min(kids.length - 1, focus + 1);
        kids[focus].focus();
      } else if (e.key === "ArrowLeft") {
        focus = Math.max(0, focus - 1);
        kids[focus].focus();
      } else if (e.key === " ") {
        e.preventDefault();
        kids[focus]?.click();
      }
    };
  }

  async function toggle(w, btn) {
    const next = !w.deleted;
    btn.classList.add("striking");
    requestAnimationFrame(() => btn.classList.toggle("on", next));
    try {
      await post("/words/delete", { word_id: w.id, deleted: next });
      const project = await get("/project");
      setState({ project });
      flashSaved();
      render();
    } catch (e) {
      toast(String(e.message || e), "danger");
      render();
    }
  }

  async function runTranscribe() {
    const prog = el.querySelector(".tprog");
    prog.hidden = false;
    const bar = progressBar(0.05, true);
    prog.appendChild(bar);
    try {
      const { job_id } = await post("/jobs/transcribe", {});
      for (;;) {
        const j = await get(`/jobs/${job_id}`);
        setProgress(bar, j.progress || 0.1, j.status === "running");
        if (j.status === "done") break;
        if (j.status === "error") throw new Error(j.error || "Failed");
        await new Promise((r) => setTimeout(r, 500));
      }
      setState({ project: await get("/project") });
      flashSaved();
      render();
    } catch (e) {
      toast(String(e.message || e), "danger");
    }
  }
}
