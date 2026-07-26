from __future__ import annotations

from reelwrite.edit.apply_candidate import apply_candidate
from reelwrite.models.project import Project
from reelwrite.rank.caveats import caveat_warnings


def register(sub):
    p = sub.add_parser("select", help="Apply candidate by deleting words outside span")
    p.add_argument("project")
    p.add_argument("candidate_id")
    p.set_defaults(func=run)


def run(args) -> int:
    project = Project.load(args.project)
    cand = next((c for c in project.candidates if c.get("id") == args.candidate_id), None)
    if not cand:
        raise SystemExit(f"Unknown candidate: {args.candidate_id}")
    project.words = apply_candidate(
        project.words, cand["word_start_id"], cand["word_end_id"]
    )
    warns = caveat_warnings(
        project.words, cand["word_start_id"], cand["word_end_id"]
    )
    for w in warns:
        print(f"WARNING: {w}")
    project.save(args.project)
    print(f"selected={args.candidate_id}")
    return 0
