from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from reelwrite.models.word import Word


def load_markers() -> list[str]:
    try:
        ref = resources.files("reelwrite").joinpath("config/caveat_markers.json")
        data = json.loads(ref.read_text(encoding="utf-8"))
    except Exception:
        p = Path(__file__).resolve().parents[1] / "config" / "caveat_markers.json"
        data = json.loads(p.read_text(encoding="utf-8"))
    return [m.lower() for m in data.get("markers", [])]


def caveat_warnings(words: list[Word], start_id: int, end_id: int) -> list[str]:
    """Warn when caveat language sits just outside the selected span."""
    markers = load_markers()
    kept = {w.id for w in words if start_id <= w.id <= end_id}
    outside = [w for w in words if w.id not in kept]
    warnings: list[str] = []
    # Check nearby context (±8 words)
    nearby = [
        w for w in outside
        if (start_id - 8) <= w.id < start_id or end_id < w.id <= (end_id + 8)
    ]
    text = " ".join(w.text.lower() for w in nearby)
    for m in markers:
        if m in text:
            warnings.append(
                f"Possible caveat language near selection: '{m}'. "
                "Verify the claim remains accurate without surrounding qualifications."
            )
            break
    return warnings
