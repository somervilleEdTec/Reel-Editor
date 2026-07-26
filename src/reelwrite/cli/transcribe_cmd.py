from __future__ import annotations

from reelwrite.workflows import transcribe_project


def register(sub):
    p = sub.add_parser("transcribe", help="Transcribe project source audio")
    p.add_argument("project")
    p.add_argument("--backend", choices=["local", "azure"], default="local")
    p.set_defaults(func=run)


def run(args) -> int:
    project = transcribe_project(args.project, backend=args.backend)
    print(f"words={len(project.words)}")
    return 0
