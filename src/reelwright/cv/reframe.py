from __future__ import annotations

from dataclasses import dataclass

from reelwright.cv.occlusion import Box


@dataclass
class DiarSegment:
    speaker: str
    start_s: float
    end_s: float


@dataclass
class CropKeyframe:
    t: float
    cx: float
    cy: float
    mode: str  # active_speaker|split_stacked|fixed


def associate_speakers(
    diar: list[DiarSegment],
    face_tracks: dict[str, list[tuple[float, Box]]],
) -> dict[str, str]:
    """Map diarised speaker -> face track id via motion energy heuristic."""
    energy: dict[tuple[str, str], float] = {}
    for seg in diar:
        mid = 0.5 * (seg.start_s + seg.end_s)
        for tid, samples in face_tracks.items():
            if len(samples) < 2:
                continue
            # nearest samples around mid
            nearby = [b for t, b in samples if abs(t - mid) < 1.0]
            if len(nearby) < 2:
                continue
            motion = sum(
                abs(nearby[i].x - nearby[i - 1].x) + abs(nearby[i].y - nearby[i - 1].y)
                for i in range(1, len(nearby))
            )
            energy[(seg.speaker, tid)] = energy.get((seg.speaker, tid), 0.0) + motion
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for (spk, tid), _ in sorted(energy.items(), key=lambda kv: -kv[1]):
        if spk in mapping or tid in used:
            continue
        mapping[spk] = tid
        used.add(tid)
    return mapping


def build_crop_path(
    diar: list[DiarSegment],
    mapping: dict[str, str],
    face_tracks: dict[str, list[tuple[float, Box]]],
    mode: str = "active_speaker",
    hysteresis_s: float = 1.2,
) -> list[CropKeyframe]:
    if mode == "fixed":
        return [CropKeyframe(0.0, 0.5, 0.5, mode)]
    keys: list[CropKeyframe] = []
    last_t = -1e9
    last_tid = None
    for seg in diar:
        tid = mapping.get(seg.speaker)
        if not tid or tid not in face_tracks:
            continue
        if tid == last_tid or (seg.start_s - last_t) < hysteresis_s and last_tid:
            # hold previous unless long enough
            if tid != last_tid and (seg.start_s - last_t) < hysteresis_s:
                continue
        samples = face_tracks[tid]
        box = min(samples, key=lambda tb: abs(tb[0] - seg.start_s))[1]
        cx, cy = box.x + box.w / 2, box.y + box.h / 2
        keys.append(CropKeyframe(seg.start_s, cx, cy, mode))
        last_t, last_tid = seg.start_s, tid
    if not keys:
        keys = [CropKeyframe(0.0, 0.5, 0.5, mode)]
    return smooth_path(keys)


def smooth_path(keys: list[CropKeyframe], alpha: float = 0.35) -> list[CropKeyframe]:
    if len(keys) < 2:
        return keys
    out = [keys[0]]
    for k in keys[1:]:
        prev = out[-1]
        out.append(
            CropKeyframe(
                k.t,
                prev.cx * (1 - alpha) + k.cx * alpha,
                prev.cy * (1 - alpha) + k.cy * alpha,
                k.mode,
            )
        )
    return out
