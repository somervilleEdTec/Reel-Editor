from __future__ import annotations

from reelwright.asr.cloud import AzureSpeechBackend
from reelwright.asr.local_whisper import LocalWhisper
from reelwright.models.project import Project


def register(sub):
    p = sub.add_parser("transcribe", help="Transcribe project source audio")
    p.add_argument("project")
    p.add_argument("--backend", choices=["local", "azure"], default="local")
    p.set_defaults(func=run)


def run(args) -> int:
    project = Project.load(args.project)
    if not project.sources:
        raise SystemExit("No sources in project")
    src = project.sources[0]
    backend = LocalWhisper() if args.backend == "local" else AzureSpeechBackend()
    project.words = backend.transcribe(src.path, src.id)
    project.save(args.project)
    print(f"words={len(project.words)}")
    return 0
