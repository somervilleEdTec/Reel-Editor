from pathlib import Path

from reelwright.captions.ass import caption_events, render_ass
from reelwright.edit.edl import Segment
from reelwright.edit.timeline import Timeline
from reelwright.models.project import Project
from reelwright.models.source import Source
from reelwright.models.word import Word


def test_caption_events_use_output_time():
    words = [
        Word(id=0, text="Hello", start_s=2.0, end_s=2.2, source_id="s"),
        Word(id=1, text="world", start_s=2.2, end_s=2.5, source_id="s"),
    ]
    tl = Timeline([Segment("s", 2.0, 2.5)])
    ev = caption_events(words, tl, max_visible=2)
    assert len(ev) == 1
    assert abs(ev[0]["start"] - 0.0) < 1e-6
    assert abs(ev[0]["end"] - 0.5) < 1e-6


def test_render_ass_file(tmp_path: Path):
    project = Project(
        sources=[Source(id="s", path="/tmp/x.mp4")],
        words=[Word(id=0, text="Hi", start_s=0.1, end_s=0.3, source_id="s")],
    )
    tl = Timeline([Segment("s", 0.0, 1.0)])
    out = tmp_path / "c.ass"
    render_ass(project, tl, str(out))
    text = out.read_text(encoding="utf-8")
    assert "Dialogue:" in text
    assert "HI" in text or "Hi" in text
