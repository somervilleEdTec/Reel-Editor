import subprocess
from pathlib import Path

from reelwrite.edit.edl import Segment
from reelwrite.edit.timeline import Timeline
from reelwrite.models.assembly import Assembly, AssemblyClip
from reelwrite.models.editing import Title
from reelwrite.models.project import Project
from reelwrite.models.source import Source
from reelwrite.models.word import Word
from reelwrite.render.assembly_filters import build_assembly_filters
from reelwrite.render.edl_filters import build_edl_av_filters
from reelwrite.render.ffmpeg import export_master
from reelwrite.render.title_filters import build_title_filters


def test_edl_filters_concat_audio_and_video():
    edl = [Segment("narr", 0.0, 1.0), Segment("narr", 1.2, 2.0)]
    sources = {"narr": Source(id="narr", path="narr.mp4", duration_s=5.0, has_audio=True)}
    parts, vlabel, alabel, duration = build_edl_av_filters(
        edl,
        {"narr": 0},
        sources,
        1080,
        1920,
        "cut",
        0.0,
    )
    graph = ";".join(parts)
    assert "concat=n=2:v=1:a=0[basev]" in graph
    assert "concat=n=2:v=0:a=1[basea]" in graph
    assert vlabel == "[basev]" and alabel == "[basea]"
    assert duration > 1.7


def test_edl_filters_crossfade_audio_and_video():
    edl = [Segment("narr", 0.0, 1.0), Segment("narr", 1.0, 2.0)]
    parts, vlabel, alabel, duration = build_edl_av_filters(
        edl,
        {"narr": 0},
        {"narr": Source(id="narr", path="narr.mp4", duration_s=10.0, has_audio=True)},
        1080,
        1920,
        "crossfade",
        0.3,
    )
    graph = ";".join(parts)
    assert "xfade=transition=fade:duration=0.3" in graph
    assert "acrossfade=d=0.3:c1=tri:c2=tri" in graph
    assert vlabel.startswith("[vx") and alabel.startswith("[ax")
    assert duration < 2.0


def test_assembly_filters_hold_and_audio_mix():
    words = [
        Word(id=0, text="one", start_s=0.0, end_s=0.4, source_id="narr"),
        Word(id=1, text="two", start_s=3.0, end_s=3.4, source_id="narr"),
    ]
    timeline = Timeline([Segment("narr", 0.0, 4.0)])
    assembly = Assembly(
        narration_source_id="narr",
        clips=[
            AssemblyClip(
                id="c1",
                source_id="broll",
                in_s=0.0,
                word_start_id=0,
                word_end_id=1,
                mute_source_audio=False,
                duration_strategy="hold",
            )
        ],
    )
    sources = {
        "narr": Source(id="narr", path="narr.mp4", duration_s=10.0, has_audio=True),
        "broll": Source(id="broll", path="b.mp4", duration_s=1.0, has_audio=True),
    }
    parts, vlabel, alabel = build_assembly_filters(
        assembly,
        words,
        timeline,
        {"narr": 0, "broll": 1},
        sources,
        1080,
        1920,
        "[basev]",
        "[basea]",
    )
    graph = ";".join(parts)
    assert "tpad=stop_mode=clone" in graph
    assert "overlay=shortest=1:enable='between(t,0,3.4)'" in graph
    assert "adelay=0:all=1" in graph
    assert "amix=inputs=2:duration=first" in graph
    assert vlabel == "[ov0]" and alabel == "[asma]"


def test_assembly_filters_slow_strategy_sets_pts():
    words = [
        Word(id=0, text="one", start_s=0.0, end_s=0.4, source_id="narr"),
        Word(id=1, text="two", start_s=3.0, end_s=3.4, source_id="narr"),
    ]
    timeline = Timeline([Segment("narr", 0.0, 4.0)])
    assembly = Assembly(
        narration_source_id="narr",
        clips=[
            AssemblyClip(
                id="c1",
                source_id="broll",
                in_s=0.0,
                word_start_id=0,
                word_end_id=1,
                mute_source_audio=True,
                duration_strategy="slow",
            )
        ],
    )
    parts, _, _ = build_assembly_filters(
        assembly,
        words,
        timeline,
        {"narr": 0, "broll": 1},
        {
            "narr": Source(id="narr", path="narr.mp4", duration_s=10.0, has_audio=True),
            "broll": Source(id="broll", path="b.mp4", duration_s=1.0, has_audio=True),
        },
        1080,
        1920,
        "[basev]",
        "[basea]",
    )
    graph = ";".join(parts)
    assert "setpts=PTS/" in graph
    assert "tpad=stop_mode=clone" not in graph


def test_title_filters_drawtext_escaping():
    titles = [
        Title(
            text="Hello:world",
            start_out_s=0.5,
            end_out_s=1.5,
            y=0.2,
            style={"box": True},
        )
    ]
    parts, out_label = build_title_filters(titles, "[capv]", 1080, 1920)
    graph = ";".join(parts)
    assert r"text='Hello\:world'" in graph
    assert "drawtext=" in graph
    assert "enable='between(t,0.5,1.5)'" in graph
    assert out_label == "[title0]"


def test_export_master_uses_edl_audio_when_no_assembly(monkeypatch, tmp_path):
    calls = []
    project = _project_with_words(tmp_path, assembly=None)
    _mock_export_subprocess(monkeypatch, calls)
    export_master(project, str(tmp_path / "master.mp4"), fmt="mp4")
    cmd = calls[0]
    vf = cmd[cmd.index("-filter_complex") + 1]
    assert cmd.count("-i") == 1
    assert "[outa]" in cmd
    assert "atrim=start=" in vf
    assert "overlay=shortest=1" not in vf


def test_export_master_uses_assembly_compositing(monkeypatch, tmp_path):
    calls = []
    assembly = Assembly(
        narration_source_id="narr",
        clips=[
            AssemblyClip(
                id="c1",
                source_id="broll",
                in_s=0.0,
                word_start_id=0,
                word_end_id=1,
                duration_strategy="hold",
            )
        ],
    )
    project = _project_with_words(tmp_path, assembly=assembly)
    _mock_export_subprocess(monkeypatch, calls)
    export_master(project, str(tmp_path / "master.mp4"), fmt="mp4")
    cmd = calls[0]
    vf = cmd[cmd.index("-filter_complex") + 1]
    assert cmd.count("-i") == 2
    assert "overlay=shortest=1:enable='between(t" in vf


def test_export_master_skips_assembly_when_no_clips(monkeypatch, tmp_path):
    calls = []
    project = _project_with_words(tmp_path, assembly=Assembly(narration_source_id="narr", clips=[]))
    _mock_export_subprocess(monkeypatch, calls)
    export_master(project, str(tmp_path / "master.mp4"), fmt="mp4")
    cmd = calls[0]
    vf = cmd[cmd.index("-filter_complex") + 1]
    assert cmd.count("-i") == 1
    assert "overlay=shortest=1" not in vf


def _project_with_words(tmp_path: Path, assembly: Assembly | None) -> Project:
    return Project(
        sources=[
            Source(id="narr", path=str(tmp_path / "narr.mp4"), duration_s=8.0, has_audio=True),
            Source(id="broll", path=str(tmp_path / "broll.mp4"), role="media", duration_s=2.0),
        ],
        words=[
            Word(id=0, text="hello", start_s=0.1, end_s=0.4, source_id="narr"),
            Word(id=1, text="world", start_s=1.0, end_s=1.3, source_id="narr"),
        ],
        assembly=assembly,
    )


def _mock_export_subprocess(monkeypatch, calls: list[list[str]]) -> None:
    def fake_render_ass(_project, _timeline, out_path: str) -> str:
        Path(out_path).write_text("", encoding="utf-8")
        return out_path

    def fake_run(cmd, capture_output=True, text=True, timeout=None):  # noqa: ARG001
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("reelwrite.render.ffmpeg.render_ass", fake_render_ass)
    monkeypatch.setattr("reelwrite.render.ffmpeg.subprocess.run", fake_run)
