from __future__ import annotations

from reelwrite.cv.occlusion import Box
from reelwrite.cv.diarise import diarise_from_words
from reelwrite.cv.reframe import (
    CropKeyframe,
    associate_speakers,
    build_crop_path,
)
from reelwrite.models.project import Project


def attach_reframe(
    project: Project,
    mode: str,
    crop_path: list[CropKeyframe],
    warnings: list[str] | None = None,
) -> Project:
    project.schema_version = max(project.schema_version, 2)
    project.reframe = {
        "mode": mode,
        "crop_path": [
            {"t": k.t, "cx": k.cx, "cy": k.cy, "mode": k.mode} for k in crop_path
        ],
        "warnings": warnings or [],
    }
    return project


def project_reframe(project: Project, mode: str = "active_speaker") -> Project:
    diarisation = diarise_from_words(project.words)
    tracks = {
        "f1": [(0.0, Box(0.25, 0.3, 0.2, 0.25))],
        "f2": [(0.0, Box(0.65, 0.3, 0.2, 0.25))],
    }
    mapping = associate_speakers(diarisation, tracks) if mode != "fixed" else {}
    path = build_crop_path(diarisation, mapping, tracks, mode=mode)
    return attach_reframe(project, mode, path)


def crop_resolution_warning(
    source_w: int, source_h: int, crop: Box, export_w: int, export_h: int
) -> str | None:
    cw, ch = crop.w * source_w, crop.h * source_h
    if cw < export_w or ch < export_h:
        return (
            f"Crop region {cw:.0f}x{ch:.0f} is below export {export_w}x{export_h}; "
            "upscaling will be required."
        )
    return None
