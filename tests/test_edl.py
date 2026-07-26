from reelwrite.edit.edl import derive_edl
from reelwrite.models.word import Word


def _words(pairs):
    out = []
    for i, (t, a, b, deleted) in enumerate(pairs):
        out.append(
            Word(id=i, text=t, start_s=a, end_s=b, source_id="s", deleted=deleted)
        )
    return out


def test_edl_basic_pads():
    words = _words([("a", 1.0, 1.2, False), ("b", 1.2, 1.5, False)])
    segs = derive_edl(words, source_duration_s=10)
    assert len(segs) == 1
    assert abs(segs[0].in_s - 0.94) < 1e-6
    assert abs(segs[0].out_s - 1.62) < 1e-6


def test_edl_deleted_splits_runs():
    words = _words(
        [
            ("a", 0.0, 0.2, False),
            ("b", 0.2, 0.4, True),
            ("c", 1.0, 1.2, False),
        ]
    )
    segs = derive_edl(words, source_duration_s=5)
    assert len(segs) == 2


def test_edl_merge_small_gap():
    words = _words(
        [
            ("a", 0.0, 0.2, False),
            ("b", 0.25, 0.4, False),  # gap after pads still small
        ]
    )
    # Make non-consecutive ids to force two runs then merge
    words[1].id = 5
    segs = derive_edl(words, source_duration_s=5, lead_pad=0, tail_pad=0, min_gap=0.2)
    assert len(segs) == 1
