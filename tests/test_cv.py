from reelwrite.cv.diarise import diarise_from_words
from reelwrite.cv.occlusion import Box, occlusion_warnings
from reelwrite.cv.reframe import associate_speakers, build_crop_path, smooth_path
from reelwrite.cv.reframe import DiarSegment
from reelwrite.models.word import Word


def test_occlusion_intersects():
    warns = occlusion_warnings(
        [Box(0.1, 0.1, 0.2, 0.2)],
        [],
        Box(0.15, 0.15, 0.2, 0.2),
        Box(0.6, 0.6, 0.2, 0.1),
    )
    assert any("Inset" in w for w in warns)


def test_associate_and_crop_path():
    diar = [DiarSegment("S1", 0, 2), DiarSegment("S2", 2.5, 4)]
    tracks = {
        "f1": [(0.0, Box(0.1, 0.2, 0.2, 0.2)), (1.0, Box(0.12, 0.21, 0.2, 0.2))],
        "f2": [(2.5, Box(0.6, 0.2, 0.2, 0.2)), (3.0, Box(0.62, 0.22, 0.2, 0.2))],
    }
    mapping = associate_speakers(diar, tracks)
    path = build_crop_path(diar, mapping, tracks, hysteresis_s=1.2)
    assert path
    assert path[0].mode == "active_speaker"


def test_smooth_path_monotonic_time():
    from reelwrite.cv.reframe import CropKeyframe

    keys = [
        CropKeyframe(0, 0.2, 0.2, "active_speaker"),
        CropKeyframe(1, 0.8, 0.2, "active_speaker"),
    ]
    out = smooth_path(keys)
    assert out[0].t <= out[1].t


def test_diarise_from_words():
    words = [
        Word(id=0, text="a", start_s=0, end_s=0.2, source_id="s", speaker="S1"),
        Word(id=1, text="b", start_s=0.3, end_s=0.5, source_id="s", speaker="S1"),
        Word(id=2, text="c", start_s=2.0, end_s=2.2, source_id="s", speaker="S2"),
    ]
    segs = diarise_from_words(words)
    assert len(segs) >= 2
