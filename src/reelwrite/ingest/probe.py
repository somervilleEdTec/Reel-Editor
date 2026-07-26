from __future__ import annotations

import json
import subprocess
from pathlib import Path

from reelwrite.models.source import Role, Source


def probe(path: str, source_id: str = "src_1", role: Role = "camera") -> Source:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", path,
    ]
    raw = subprocess.check_output(cmd, text=True)
    data = json.loads(raw)
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    rot = 0
    tags = v.get("tags") or {}
    if "rotate" in tags:
        rot = int(tags["rotate"])
    for side in v.get("side_data_list") or []:
        if "rotation" in side:
            rot = int(side["rotation"])
    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    if abs(rot) in (90, 270):
        w, h = h, w
    fps = _parse_fps(v.get("r_frame_rate") or "30/1")
    dur = float(data.get("format", {}).get("duration") or v.get("duration") or 0)
    return Source(
        id=source_id, path=str(Path(path).resolve()), role=role,
        duration_s=dur, width=w, height=h, fps=fps,
        has_audio=a is not None,
        sample_rate=int(a["sample_rate"]) if a and a.get("sample_rate") else None,
        rotation=rot,
    )


def _parse_fps(rate: str) -> float:
    if "/" in rate:
        n, d = rate.split("/", 1)
        return float(n) / float(d) if float(d) else 30.0
    return float(rate or 30)
