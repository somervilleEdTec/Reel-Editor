import shutil
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from reelwright.api.app import app, resolve_export_out
from reelwright.models.project import Project
from reelwright.models.source import Source
from reelwright.models.word import Word
from reelwright.edit.edl import Segment
from reelwright.render.ffmpeg import (
    _build_filter,
    _codec_args,
    _escape_filter_path,
    _stderr_tail,
)


def _open_project(c, tmp_path):
    p = Project(
        sources=[Source(id="s", path=str(tmp_path / "missing.mp4"))],
        words=[Word(id=0, text="Hi", start_s=0, end_s=0.2, source_id="s")],
    )
    path = tmp_path / "proj" / "project.json"
    path.parent.mkdir()
    p.save(str(path))
    assert c.post("/project/open", json={"path": str(path)}).status_code == 200
    return path


def test_formats_endpoint():
    c = TestClient(app)
    data = c.get("/formats").json()
    assert {f["key"] for f in data["output"]} >= {"mp4", "mov", "webm", "mkv"}
    assert data["default"] == "mp4"
    assert ".mts" in data["input_exts"]


def test_bare_filename_lands_in_project_dir(tmp_path):
    proj = _open_project(TestClient(app), tmp_path)
    out, fmt = resolve_export_out("master.mp4", None)
    assert fmt == "mp4"
    assert Path(out).parent == proj.parent


def test_extension_follows_chosen_format(tmp_path):
    _open_project(TestClient(app), tmp_path)
    out, fmt = resolve_export_out("master.mp4", "webm")
    assert fmt == "webm" and out.endswith("master.webm")
    out, _ = resolve_export_out("clip.avi", "mkv")  # input-only ext gets replaced
    assert out.endswith("clip.mkv")
    out, fmt = resolve_export_out("plain", None)
    assert fmt == "mp4" and out.endswith("plain.mp4")


def test_format_inferred_from_extension(tmp_path):
    _open_project(TestClient(app), tmp_path)
    assert resolve_export_out("reel.webm", None)[1] == "webm"
    assert resolve_export_out("reel.mov", None)[1] == "mov"


def test_unknown_format_rejected(tmp_path):
    _open_project(TestClient(app), tmp_path)
    with pytest.raises(HTTPException) as e:
        resolve_export_out("master.mp4", "avi")
    assert e.value.status_code == 400


def test_codec_args_per_format():
    mp4 = _codec_args("mp4")
    assert "libx264" in mp4 and "+faststart" in mp4
    mov = _codec_args("mov")
    assert "libx264" in mov and "+faststart" in mov
    mkv = _codec_args("mkv")
    assert "libx264" in mkv and "+faststart" not in mkv
    webm = _codec_args("webm")
    assert any(a.startswith("libvpx") for a in webm)
    assert "+faststart" not in webm and "libx264" not in webm


def test_stderr_tail_keeps_last_lines():
    long = "\n".join(f"line{i}" for i in range(100))
    tail = _stderr_tail(long)
    assert "line99" in tail and "line0\n" not in tail
    assert _stderr_tail(None) == "no ffmpeg output"
    assert _stderr_tail("") == "no ffmpeg output"


def test_duplicate_export_to_same_path_rejected(tmp_path):
    import threading

    from reelwright.jobs.queue import QUEUE

    c = TestClient(app)
    _open_project(c, tmp_path)
    out, _ = resolve_export_out("master.mp4", "mp4")
    release = threading.Event()
    blocker = QUEUE.submit("export", lambda job: release.wait(5), meta={"out": out})
    try:
        res = c.post("/jobs/export", json={"out": "master.mp4", "format": "mp4"})
        assert res.status_code == 409
        res2 = c.post("/jobs/export", json={"out": "other.mp4", "format": "mp4"})
        assert res2.status_code == 200  # different target file is fine
    finally:
        release.set()
        QUEUE.cancel(blocker.id)


def test_escape_filter_path_quotes_windows_drive():
    """Drive-letter ':' must not become an ffmpeg option separator."""
    win = r"C:\Users\tomso\AppData\Local\Temp\reelwright-f22067cw\captions.ass"
    esc = _escape_filter_path(win)
    assert esc.startswith("'") and esc.endswith("'")
    assert r"C\:/" in esc
    assert "AppData/Local/Temp" in esc
    # Unquoted backslash-only escape is insufficient on Windows ffmpeg.
    assert esc != r"C\:/Users/tomso/AppData/Local/Temp/reelwright-f22067cw/captions.ass"


def test_build_filter_embeds_quoted_ass_path():
    project = Project(
        sources=[Source(id="s", path="x.mp4")],
        words=[Word(id=0, text="Hi", start_s=0, end_s=0.2, source_id="s")],
    )
    vf = _build_filter(
        [Segment("s", 0.0, 1.0)],
        project,
        r"C:\Users\tomso\AppData\Local\Temp\reelwright-x\captions.ass",
    )
    assert "subtitles='C\\:/Users/tomso/" in vf
    assert vf.endswith("[outv]")


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_subtitles_filter_accepts_colon_in_path(tmp_path):
    """Reproduce Windows original_size bug: colon path must parse as filename."""
    import subprocess

    media = tmp_path / "in.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=c=black:s=320x240:d=0.2",
            "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono",
            "-t", "0.2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            str(media),
        ],
        check=True,
        capture_output=True,
    )
    # Linux allows ':' in directory names — mimics Windows drive separator.
    colon_dir = tmp_path / "C:"
    colon_dir.mkdir()
    ass = colon_dir / "captions.ass"
    ass.write_text(
        "[Script Info]\nScriptType: v4.00+\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Arial,24,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,"
        "0,0,0,0,100,100,0,0,1,0,0,2,10,10,10,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        "Dialogue: 0,0:00:00.00,0:00:00.20,Default,,0,0,0,,Hi\n"
    )
    filt = f"[0:v]subtitles={_escape_filter_path(str(ass))}[outv]"
    out = tmp_path / "out.mp4"
    proc = subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-i", str(media),
            "-filter_complex", filt, "-map", "[outv]", "-frames:v", "1", str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "original_size" not in (proc.stderr or "")
    assert out.exists()


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_export_job_surfaces_ffmpeg_stderr(tmp_path):
    import time

    c = TestClient(app)
    _open_project(c, tmp_path)
    res = c.post("/jobs/export", json={"out": "master.mp4", "aspect": None, "format": "mp4"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["format"] == "mp4" and body["out"].endswith("master.mp4")
    job = None
    for _ in range(100):
        job = c.get(f"/jobs/{body['job_id']}").json()
        if job["status"] in ("done", "error", "cancelled"):
            break
        time.sleep(0.05)
    assert job["status"] == "error"
    assert "ffmpeg failed" in (job["error"] or "")
