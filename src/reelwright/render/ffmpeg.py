from __future__ import annotations

import functools
import subprocess
import tempfile
from pathlib import Path

from reelwright.captions.ass import render_ass
from reelwright.edit.edl import derive_edl
from reelwright.edit.timeline import Timeline
from reelwright.media_formats import DEFAULT_OUTPUT_FORMAT, OUTPUT_FORMATS, format_for_ext
from reelwright.models.project import Project
from reelwright.render.profiles import apply_profile


def export_master(
    project: Project,
    out_path: str,
    aspect: str | None = None,
    fmt: str | None = None,
) -> str:
    apply_profile(project, aspect)
    fmt = fmt or format_for_ext(Path(out_path).suffix) or DEFAULT_OUTPUT_FORMAT
    if fmt not in OUTPUT_FORMATS:
        raise ValueError(f"Unsupported export format: {fmt}")
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
            "ffmpeg", "-y", "-hide_banner", "-threads", "1", "-i", src.path,
            "-filter_complex", vf, "-map", "[outv]", "-map", "0:a?",
            *_codec_args(fmt), "-r", str(project.export.fps), out_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed (exit {proc.returncode}): {_stderr_tail(proc.stderr)}"
            )
    return out_path


def _codec_args(fmt: str) -> list[str]:
    """Codec/container flags per output format."""
    if fmt == "webm":
        vcodec, acodec = _webm_codecs()
        args = ["-c:v", vcodec, "-pix_fmt", "yuv420p"]
        args += ["-crf", "32", "-b:v", "0"] if vcodec == "libvpx-vp9" else ["-crf", "10", "-b:v", "4M"]
        args += ["-c:a", acodec]
        args += ["-b:a", "128k"] if acodec == "libopus" else ["-q:a", "5"]
        return args + ["-ar", "48000"]
    args = [
        "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
    ]
    if fmt in ("mp4", "mov"):
        args += ["-movflags", "+faststart"]  # streaming-friendly moov atom
    return args


@functools.lru_cache(maxsize=1)
def _webm_codecs() -> tuple[str, str]:
    """Prefer VP9/Opus; fall back to VP8/Vorbis when encoders are missing."""
    try:
        out = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True, timeout=15,
        ).stdout or ""
    except Exception:
        return ("libvpx-vp9", "libopus")
    if not out.strip():
        return ("libvpx-vp9", "libopus")
    vcodec = "libvpx-vp9" if "libvpx-vp9" in out else "libvpx"
    acodec = "libopus" if "libopus" in out else "libvorbis"
    return (vcodec, acodec)


def _stderr_tail(stderr: str | None, lines: int = 12, limit: int = 2000) -> str:
    tail = "\n".join((stderr or "").strip().splitlines()[-lines:])
    return tail[-limit:] or "no ffmpeg output"


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
