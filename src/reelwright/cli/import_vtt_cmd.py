from __future__ import annotations

from reelwright.asr.align import import_vtt
from reelwright.models.project import Project, TranscriptImport


def register(sub):
    p = sub.add_parser("import-vtt", help="Import Zoom WebVTT (force-align approx)")
    p.add_argument("project")
    p.add_argument("vtt")
    p.set_defaults(func=run)


def run(args) -> int:
    project = Project.load(args.project)
    if not project.sources:
        raise SystemExit("No sources in project")
    sid = project.sources[0].id
    project.words = import_vtt(args.vtt, sid)
    project.transcript_import = TranscriptImport(path=args.vtt, aligned=True)
    project.save(args.project)
    print(f"words={len(project.words)}")
    return 0
