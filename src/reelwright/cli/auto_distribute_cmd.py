from __future__ import annotations

from reelwright.assembly.distribute import auto_distribute
from reelwright.models.project import Project


def register(sub):
    p = sub.add_parser("auto-distribute", help="Distribute clips across narration words")
    p.add_argument("project")
    p.add_argument("--narration", default=None, help="narration source id")
    p.set_defaults(func=run)


def run(args) -> int:
    project = Project.load(args.project)
    narr = args.narration
    if not narr:
        vo = next((s for s in project.sources if s.role == "voiceover"), None)
        narr = vo.id if vo else (project.sources[0].id if project.sources else "")
    clips = [s for s in project.sources if s.role == "media"]
    project.assembly = auto_distribute(narr, clips, project.words)
    project.save(args.project)
    print(f"assembly_clips={len(project.assembly.clips)}")
    return 0
