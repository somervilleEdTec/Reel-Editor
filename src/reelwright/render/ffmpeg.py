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
from reelwright.models.source import Source
from reelwright.render.assembly_filters import build_assembly_filters
from reelwright.render.edl_filters import build_edl_av_filters
from reelwright.render.profiles import apply_profile
from reelwright.render.title_filters import build_title_filters


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
    if not src:
        raise RuntimeError("No source media in project")
    dur = src.duration_s if src else None
    edl = derive_edl(project.words, source_duration_s=dur)
    timeline = Timeline(edl)
    if not edl:
        raise RuntimeError("EDL empty — no retained words")
    sources = {s.id: s for s in project.sources}
    use_assembly = bool(project.assembly and project.assembly.clips)
    source_ids = _required_source_ids(project, edl, src.id, use_assembly)
    source_inputs = {sid: i for i, sid in enumerate(source_ids)}
    input_sources = [sources[sid] for sid in source_ids]
    # Safe temp ASS path avoids filter_complex metacharacters in user paths.
    with tempfile.TemporaryDirectory(prefix="reelwright-") as tmp:
        ass_path = str(Path(tmp) / "captions.ass")
        render_ass(project, timeline, ass_path)
        vf = _build_export_filter(
            edl, project, timeline, ass_path, source_inputs, sources, use_assembly
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-threads",
            "1",
            *_input_args(input_sources),
            "-filter_complex",
            vf,
            "-map",
            "[outv]",
            "-map",
            "[outa]",
            *_codec_args(fmt),
            "-r",
            str(project.export.fps),
            out_path,
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
    if project.assembly and project.assembly.narration_source_id:
        sid = project.assembly.narration_source_id
        for source in project.sources:
            if source.id == sid:
                return source
    if project.words:
        sid = next((w.source_id for w in project.words if not w.deleted), None)
        for s in project.sources:
            if s.id == sid:
                return s
    return project.sources[0]


def _build_filter(edl, project: Project, ass_path: str) -> str:
    """Compatibility helper used by tests."""
    src = _primary_source(project)
    if not src:
        raise RuntimeError("No source media in project")
    timeline = Timeline(edl)
    sources = {s.id: s for s in project.sources}
    source_ids = _required_source_ids(project, edl, src.id, include_assembly=False)
    source_inputs = {sid: i for i, sid in enumerate(source_ids)}
    return _build_export_filter(
        edl, project, timeline, ass_path, source_inputs, sources, include_assembly=False
    )


def _build_export_filter(
    edl,
    project: Project,
    timeline: Timeline,
    ass_path: str,
    source_inputs: dict[str, int],
    sources: dict[str, Source],
    include_assembly: bool,
) -> str:
    w, h = project.export.width, project.export.height
    parts, video_label, audio_label, _ = build_edl_av_filters(
        edl,
        source_inputs,
        sources,
        w,
        h,
        project.export.transition,
        project.export.transition_s,
    )
    if include_assembly and project.assembly and project.assembly.clips:
        asm_parts, video_label, audio_label = build_assembly_filters(
            project.assembly,
            project.words,
            timeline,
            source_inputs,
            sources,
            w,
            h,
            video_label,
            audio_label,
        )
        parts.extend(asm_parts)
    parts.append(f"{video_label}subtitles={_escape_filter_path(ass_path)}[capv]")
    video_label = "[capv]"
    title_parts, video_label = build_title_filters(project.titles, video_label, w, h)
    parts.extend(title_parts)
    parts.append(f"{audio_label}anull[outa]")
    parts.append(f"{video_label}format=yuv420p[outv]")
    return ";".join(parts)


def _required_source_ids(
    project: Project, edl, primary_source_id: str, include_assembly: bool
) -> list[str]:
    known = {source.id for source in project.sources}
    ids: list[str] = []

    def add(source_id: str) -> None:
        if source_id in known and source_id not in ids:
            ids.append(source_id)

    add(primary_source_id)
    for seg in edl:
        add(seg.source_id)
    if include_assembly and project.assembly:
        for clip in project.assembly.clips:
            add(clip.source_id)
    return ids


def _input_args(sources: list[Source]) -> list[str]:
    args: list[str] = []
    for source in sources:
        args.extend(["-i", source.path])
    return args


def _escape_filter_path(path: str) -> str:
    """Escape a filesystem path for use inside an ffmpeg filtergraph.

    Windows absolute paths contain a drive colon (``C:/...``). Unquoted, ffmpeg
    treats ``:`` as an option separator, so ``subtitles=C:/Temp/captions.ass``
    becomes filename=``C`` and original_size=``/Temp/captions.ass``. Wrap in
    single quotes and escape ``\\``, ``'``, and ``:`` inside the quotes.
    """
    p = path.replace("\\", "/")
    inner = "".join(f"\\{ch}" if ch in "\\:'" else ch for ch in p)
    return f"'{inner}'"
