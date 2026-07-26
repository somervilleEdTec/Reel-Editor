from __future__ import annotations

from reelwrite.models.editing import Title


def build_title_filters(
    titles: list[Title], input_label: str, width: int, height: int
) -> tuple[list[str], str]:
    parts: list[str] = []
    current = input_label
    for i, title in enumerate(sorted(titles, key=lambda t: t.start_out_s)):
        if not title.text or title.end_out_s <= title.start_out_s:
            continue
        style = title.style or {}
        fontsize = int(style.get("size_px", style.get("font_size", 64)))
        fontcolor = style.get("fill", style.get("color", "#FFFFFF"))
        x = style.get("x", "(w-text_w)/2")
        y = int(max(0.0, min(1.0, title.y)) * height)
        box = 1 if style.get("box", False) else 0
        box_color = style.get("box_color", "black@0.45")
        enabled = f"between(t,{_fmt(title.start_out_s)},{_fmt(title.end_out_s)})"
        args = [
            f"text='{_escape_text(title.text)}'",
            f"x={x}",
            f"y={y}",
            f"fontsize={fontsize}",
            f"fontcolor={fontcolor}",
            f"box={box}",
            f"boxcolor={box_color}",
            f"enable='{enabled}'",
        ]
        out = f"title{i}"
        parts.append(f"{current}drawtext={':'.join(args)}[{out}]")
        current = f"[{out}]"
    return parts, current


def _escape_text(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace("%", r"\%")
        .replace("\n", r"\n")
        .replace("\r", "")
    )


def _fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") or "0"
