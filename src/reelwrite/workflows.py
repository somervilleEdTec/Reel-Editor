"""Create project from video and run transcription (shared by CLI and API)."""

from __future__ import annotations

from pathlib import Path

from reelwrite.asr.local_whisper import LocalWhisper
from reelwrite.ingest.probe import probe
from reelwrite.models.project import Project


def init_project(video: str, out: str, role: str = "camera") -> Project:
    src = probe(video, source_id="src_1", role=role)
    project = Project(sources=[src])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    project.save(out)
    return project


def transcribe_project(project_path: str, backend: str = "local") -> Project:
    project = Project.load(project_path)
    if not project.sources:
        raise RuntimeError("No sources in project")
    src = project.sources[0]
    if backend == "azure":
        from reelwrite.asr.cloud import AzureSpeechBackend

        asr = AzureSpeechBackend()
    else:
        asr = LocalWhisper()
    project.words = asr.transcribe(src.path, src.id)
    project.save(project_path)
    return project
