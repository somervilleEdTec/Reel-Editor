"""Golden sync: caption event starts within 80ms of mapped word times."""

from reelwright.captions.ass import caption_events
from reelwright.edit.edl import derive_edl
from reelwright.edit.timeline import Timeline
from reelwright.models.word import Word


def test_golden_sync_within_80ms():
    words = [
        Word(id=0, text="There", start_s=0.42, end_s=0.61, source_id="cam"),
        Word(id=1, text="is", start_s=0.62, end_s=0.75, source_id="cam"),
        Word(id=2, text="risk", start_s=0.76, end_s=1.05, source_id="cam"),
    ]
    edl = derive_edl(words, source_duration_s=10)
    tl = Timeline(edl)
    events = caption_events(words, tl, max_visible=3)
    assert events
    # First word output start should match timeline mapping within 80ms
    expected = tl.source_to_output("cam", 0.42)
    assert expected is not None
    assert abs(events[0]["start"] - expected) <= 0.08
