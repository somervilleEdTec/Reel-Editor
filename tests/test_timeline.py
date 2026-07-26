from reelwright.edit.edl import Segment
from reelwright.edit.timeline import Timeline


def test_source_to_output():
    tl = Timeline([Segment("s", 1.0, 3.0), Segment("s", 5.0, 6.0)])
    assert abs(tl.source_to_output("s", 1.0) - 0.0) < 1e-6
    assert abs(tl.source_to_output("s", 2.0) - 1.0) < 1e-6
    assert abs(tl.source_to_output("s", 5.5) - 2.5) < 1e-6
    assert tl.duration_s == 3.0


def test_output_to_source():
    tl = Timeline([Segment("s", 10.0, 12.0)])
    sid, t = tl.output_to_source(0.5)
    assert sid == "s"
    assert abs(t - 10.5) < 1e-6
