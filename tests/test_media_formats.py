from reelwrite.media_formats import (
    DEFAULT_OUTPUT_FORMAT,
    MEDIA_TYPES,
    OUTPUT_FORMATS,
    VIDEO_EXTS,
    format_for_ext,
)


def test_video_exts_cover_common_camera_formats():
    expected = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi",
                ".mts", ".m2ts", ".wmv", ".flv", ".3gp", ".ts"}
    assert expected <= VIDEO_EXTS


def test_media_types_cover_every_video_ext():
    assert VIDEO_EXTS <= set(MEDIA_TYPES)
    assert {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"} <= set(MEDIA_TYPES)


def test_format_for_ext_case_insensitive():
    assert format_for_ext(".MP4") == "mp4"
    assert format_for_ext(".webm") == "webm"
    assert format_for_ext(".avi") is None  # input-only ext has no output format


def test_output_formats_shape():
    assert DEFAULT_OUTPUT_FORMAT in OUTPUT_FORMATS
    assert {"mp4", "mov", "webm", "mkv"} <= set(OUTPUT_FORMATS)
    for key, spec in OUTPUT_FORMATS.items():
        assert spec["ext"] == f".{key}"
        assert spec["label"]
