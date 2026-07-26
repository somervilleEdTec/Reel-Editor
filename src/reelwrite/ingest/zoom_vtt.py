from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VttCue:
    start_s: float
    end_s: float
    text: str
    speaker: str | None = None


_TS = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s-->\s(\d{2}):(\d{2}):(\d{2})\.(\d{3})"
)
_SPEAKER = re.compile(r"^([^:]+):\s*(.*)$")


def parse_webvtt(path: str) -> list[VttCue]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    cues: list[VttCue] = []
    i = 0
    while i < len(lines):
        m = _TS.search(lines[i])
        if not m:
            i += 1
            continue
        start = _to_s(m)
        end = _to_s(m, offset=4)
        i += 1
        text_lines: list[str] = []
        while i < len(lines) and lines[i].strip():
            text_lines.append(lines[i].strip())
            i += 1
        raw = " ".join(text_lines)
        speaker, text = _split_speaker(raw)
        cues.append(VttCue(start, end, text, speaker))
    return cues


def _to_s(m: re.Match, offset: int = 0) -> float:
    h, mi, s, ms = (int(m.group(offset + k)) for k in range(1, 5))
    return h * 3600 + mi * 60 + s + ms / 1000.0


def _split_speaker(raw: str) -> tuple[str | None, str]:
    m = _SPEAKER.match(raw)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None, raw
