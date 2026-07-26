from __future__ import annotations

import json
from importlib import resources
from pathlib import Path


def load_aspects() -> dict:
    try:
        ref = resources.files("reelwrite").joinpath("config/aspects.json")
        return json.loads(ref.read_text(encoding="utf-8"))
    except Exception:
        p = Path(__file__).resolve().parents[1] / "config" / "aspects.json"
        return json.loads(p.read_text(encoding="utf-8"))


def apply_profile(project, profile_name: str | None = None):
    aspects = load_aspects()
    name = profile_name or project.export.profile
    if name not in aspects:
        raise ValueError(f"Unknown profile: {name}")
    p = aspects[name]
    project.export.profile = name
    project.export.width = p["width"]
    project.export.height = p["height"]
    caps = p.get("captions") or {}
    if "y" in caps:
        project.captions.y = caps["y"]
    if "max_words_visible" in caps:
        project.captions.max_words_visible = caps["max_words_visible"]
    if "preset" in caps and not project.captions.preset:
        project.captions.preset = caps["preset"]
    return project
