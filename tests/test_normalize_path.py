from pathlib import Path

from reelwrite.paths import normalize_user_path


def test_normalize_strips_explorer_quotes(tmp_path: Path):
    f = tmp_path / "a.mp4"
    f.write_bytes(b"x")
    assert normalize_user_path(f'"{f}"') == f
    assert normalize_user_path(f"'{f}'") == f


def test_normalize_strips_bom_and_whitespace(tmp_path: Path):
    f = tmp_path / "b.mp4"
    f.write_bytes(b"x")
    assert normalize_user_path(f"\ufeff {f} \n") == f


def test_normalize_file_url(tmp_path: Path):
    f = tmp_path / "c.mp4"
    f.write_bytes(b"x")
    assert normalize_user_path(f"file://{f}") == f
