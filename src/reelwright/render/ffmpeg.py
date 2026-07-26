from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from reelwright.captions.ass import render_ass
from reelwright.edit.edl import derive_edl
from reelwright.edit.timeline import Timeline
from reelwright.models.project import Project
from reelwright.render.profiles import apply_profile


def export_master(project: Project, out_path: str, aspect: str | None = None) -> str:
    apply_profile(project, aspect)
    src = _primary_source(project)
    dur = src.duration_s if src else None
    edl = derive_edl(project.words, source_duration_s=dur)
    timeline = Timeline(edl)
    if not src:
        raise RuntimeError("No source media in project")
    if not edl:
        raise RuntimeError("EDL empty — no retained words")
    # Safe temp ASS path avoids filter_complex metacharacters in user paths.
    with tempfile.TemporaryDirectory(prefix="reelwright-") as tmp:
        ass_path = str(Path(tmp) / "captions.ass")
        render_ass(project, timeline, ass_path)
        vf = _build_filter(edl, project, ass_path)
        cmd = [
            "ffmpeg", "-y", "-threads", "1", "-i", src.path,
            "-filter_complex", vf, "-map", "[outv]", "-map", "0:a?",
            "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-crf", "18", "-r", str(project.export.fps),
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", out_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    return out_path


def _primary_source(project: Project):
    if not project.sources:
        return None
    if project.words:
        sid = next((w.source_id for w in project.words if not w.deleted), None)
        for s in project.sources:
            if s.id == sid:
                return s
    return project.sources[0]


def _build_filter(edl, project: Project, ass_path: str) -> str:
    w, h = project.export.width, project.export.height
    parts = []
    labels = []
    for i, seg in enumerate(edl):
        lab = f"v{i}"
        parts.append(
            f"[0:v]trim=start={seg.in_s}:end={seg.out_s},setpts=PTS-STARTPTS[{lab}]"
        )
        labels.append(f"[{lab}]")
    if len(labels) == 1:
        concat = f"{labels[0]}scale={w}:{h}:force_original_aspect_ratio=increase,"
        concat += f"crop={w}:{h},setsar=1[base]"
    else:
        n = len(labels)
        parts.append("".join(labels) + f"concat=n={n}:v=1:a=0[cat]")
        concat = (
            f"[cat]scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},setsar=1[base]"
        )
    parts.append(concat)
    parts.append(f"[base]subtitles={_escape_filter_path(ass_path)}[outv]")
    return ";".join(parts)


def _escape_filter_path(path: str) -> str:
    """Escape a filesystem path for use inside an ffmpeg filtergraph."""
    p = path.replace("\\", "/")
    return "".join(f"\\{ch}" if ch in "\\:'[],;" else ch for ch in p)
