from __future__ import annotations

from pathlib import Path

from reelwrite.asr.local_whisper import LocalWhisper
from reelwrite.assembly.capture import capture_voiceover
from reelwrite.ingest.probe import probe
from reelwrite.models.project import Project


def register(sub):
    p = sub.add_parser("record-vo", help="Record voiceover WAV and transcribe")
    p.add_argument("project")
    p.add_argument("-o", "--out", default="voiceover.wav")
    p.add_argument("--duration", type=float, default=3.0)
    p.set_defaults(func=run)


def run(args) -> int:
    project = Project.load(args.project)
    path = capture_voiceover(args.out, duration_s=args.duration)
    src = probe(path, source_id="src_vo", role="voiceover")
    # probe may fail on wav dimensions — set manually if needed
    if src.duration_s <= 0:
        src.duration_s = args.duration
        src.has_audio = True
    project.sources = [s for s in project.sources if s.id != "src_vo"] + [src]
    try:
        project.words = LocalWhisper().transcribe(path, "src_vo")
    except Exception as e:
        print(f"transcription deferred: {e}")
    project.save(args.project)
    print(path)
    return 0
