export function sampleCaptionText(project) {
  const words = (project?.words || []).filter((w) => !w.deleted).slice(0, 3);
  if (!words.length) return "CAPTIONS";
  return words.map((w) => w.text).join(" ");
}

export function paintCaption(el, project, presets) {
  if (!el || !project) return;
  const preset = presets?.[project.captions.preset] || {};
  const upper = project.captions.uppercase || preset.uppercase;
  el.textContent = sampleCaptionText(project);
  el.style.top = `${project.captions.y * 100}%`;
  el.style.textTransform = upper ? "uppercase" : "none";
  el.style.fontStyle = preset.italic ? "italic" : "normal";
  el.style.color = preset.fill || "#fff";
  el.style.background = preset.box || "transparent";
  el.style.padding = preset.box ? "0.35rem 0.55rem" : "0";
}
