from __future__ import annotations

from pathlib import Path

from reelwrite.asr.local_whisper import LocalWhisper
from reelwrite.ingest.probe import probe
from reelwrite.models.project import Project
from reelwrite.render.ffmpeg import export_master


def register(sub):
    p = sub.add_parser("run", help="init → transcribe → export")
    p.add_argument("video")
    p.add_argument("-o", "--out", default="master.mp4")
    p.add_argument("--project", default="project.json")
    p.add_argument("--aspect", default="portrait_9_16")
    p.set_defaults(func=run)


def run(args) -> int:
    src = probe(args.video, source_id="src_1", role="camera")
    project = Project(sources=[src])
    project.words = LocalWhisper().transcribe(src.path, src.id)
    Path(args.project).parent.mkdir(parents=True, exist_ok=True)
    project.save(args.project)
    aspect = {"9:16": "portrait_9_16", "16:9": "landscape_16_9"}.get(
        args.aspect, args.aspect
    )
    export_master(project, args.out, aspect=aspect)
    print(args.out)
    return 0
