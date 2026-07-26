from pathlib import Path

from reelwrite.asr.align import import_vtt
from reelwrite.ingest.zoom_vtt import parse_webvtt


def test_parse_webvtt(tmp_path: Path):
    p = tmp_path / "t.vtt"
    p.write_text(
        "WEBVTT\n\n"
        "00:00:01.000 --> 00:00:02.000\n"
        "Alice: Hello there\n\n"
        "00:00:02.000 --> 00:00:03.500\n"
        "Bob: Hi\n",
        encoding="utf-8",
    )
    cues = parse_webvtt(str(p))
    assert len(cues) == 2
    assert cues[0].speaker == "Alice"
    assert cues[0].text == "Hello there"


def test_align_vtt(tmp_path: Path):
    p = tmp_path / "t.vtt"
    p.write_text(
        "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHello world\n",
        encoding="utf-8",
    )
    words = import_vtt(str(p), "src")
    assert len(words) == 2
    assert words[0].text == "Hello"
    assert abs(words[0].start_s - 0.0) < 1e-6
    assert abs(words[1].end_s - 1.0) < 1e-6
