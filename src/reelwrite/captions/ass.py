from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from reelwrite.edit.timeline import Timeline
from reelwrite.models.project import Project
from reelwrite.models.word import Word


def load_presets() -> dict:
    try:
        ref = resources.files("reelwrite").joinpath("captions/presets.json")
        return json.loads(ref.read_text(encoding="utf-8"))
    except Exception:
        p = Path(__file__).with_name("presets.json")
        return json.loads(p.read_text(encoding="utf-8"))


def caption_events(
    words: list[Word], timeline: Timeline, max_visible: int = 3
) -> list[dict]:
    kept = [w for w in words if not w.deleted]
    events: list[dict] = []
    i = 0
    while i < len(kept):
        window = kept[i : i + max_visible]
        start = timeline.source_to_output(window[0].source_id, window[0].start_s)
        end = timeline.source_to_output(window[-1].source_id, window[-1].end_s)
        if start is not None and end is not None and end > start:
            events.append(
                {
                    "start": start,
                    "end": end,
                    "text": " ".join(w.text for w in window),
                }
            )
        i += max_visible
    return events


def render_ass(project: Project, timeline: Timeline, out_path: str) -> str:
    presets = load_presets()
    preset = presets.get(project.captions.preset, presets["clean"])
    events = caption_events(
        project.words, timeline, project.captions.max_words_visible
    )
    w, h = project.export.width, project.export.height
    y_px = int(project.captions.y * h)
    font = preset.get("font", "Arial")
    size = int(preset.get("size_px", 58))
    fill = _ass_color(preset.get("fill", "#FFFFFF"))
    box = preset.get("box")
    border = int(preset.get("outline_px") or 0)
    style = (
        f"Style: Default,{font},{size},{fill},&H000000FF,&H00000000,"
        f"&H80000000,{'1' if preset.get('italic') else '0'},0,0,0,100,100,"
        f"0,0,1,{border},0,{2 if box else 1},10,10,{h - y_px},1"
    )
    if box:
        # BackColour as box via BorderStyle=3
        back = _ass_color(box)
        style = (
            f"Style: Default,{font},{size},{fill},&H000000FF,&H00000000,"
            f"{back},{'1' if preset.get('italic') else '0'},0,0,0,100,100,"
            f"0,0,3,{max(border, 4)},0,2,10,10,{h - y_px},1"
        )
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {w}",
        f"PlayResY: {h}",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,"
        "BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,"
        "BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
        style,
        "",
        "[Events]",
        "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
    ]
    for ev in events:
        text = ev["text"]
        if project.captions.uppercase or preset.get("uppercase"):
            text = text.upper()
        text = _escape_ass(text)
        lines.append(
            f"Dialogue: 0,{_ts(ev['start'])},{_ts(ev['end'])},Default,,0,0,0,,{text}"
        )
    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def _escape_ass(text: str) -> str:
    """Neutralise ASS override codes and breaks in caption text."""
    return (
        text.replace("\\", "\\\\")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("\n", "\\N")
        .replace("\r", "")
    )


def _ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _ass_color(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b.upper()}{g.upper()}{r.upper()}"
