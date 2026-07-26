"""Windows Copy-as-path must not be joined onto the POSIX cwd."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from reelwrite.api.app import app
from reelwrite.paths import normalize_user_path


WIN = r'"C:\Users\tomso\Videos\WhatsApp Video 2026-07-26 at 15.06.58.mp4"'


def test_windows_drive_path_not_joined_to_cwd():
    if sys.platform == "win32":
        p = normalize_user_path(WIN)
        assert p.is_absolute()
        assert str(p).lower().startswith("c:")
        return
    with pytest.raises(ValueError, match="Windows path cannot be used"):
        normalize_user_path(WIN)


def test_windows_forward_slash_drive_path():
    raw = "C:/Users/tomso/Videos/clip.mp4"
    if sys.platform == "win32":
        assert normalize_user_path(raw).is_absolute()
        return
    with pytest.raises(ValueError, match="Windows path cannot be used"):
        normalize_user_path(raw)


def test_windows_path_maps_when_mnt_drive_exists(tmp_path, monkeypatch):
    if sys.platform == "win32":
        pytest.skip("WSL mapping is POSIX-only")
    mnt = tmp_path / "mnt"
    drive = mnt / "c"
    video = drive / "Users" / "tomso" / "Videos" / "clip.mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"x")

    real_path = Path

    class PrefixedPath(type(Path())):
        def __new__(cls, *args, **kwargs):
            if args and str(args[0]).startswith("/mnt"):
                # Rewrite absolute /mnt/... lookups into tmp_path/mnt/...
                rel = str(args[0])[1:]  # drop leading /
                return real_path(tmp_path, *rel.split("/"))
            return real_path(*args, **kwargs)

    monkeypatch.setattr("reelwrite.paths.Path", PrefixedPath)
    out = normalize_user_path(r"C:\Users\tomso\Videos\clip.mp4")
    assert out == video
    assert out.is_file()


def test_create_project_rejects_windows_path_on_posix(tmp_path, monkeypatch):
    if sys.platform == "win32":
        pytest.skip("POSIX-only assertion")
    monkeypatch.setenv("REELWRITE_DATA", str(tmp_path / "data"))
    projects = tmp_path / "projects"
    projects.mkdir()
    c = TestClient(app)
    assert c.post("/setup/projects-dir", json={"path": str(projects)}).status_code == 200
    res = c.post("/projects/create", json={"video_path": WIN})
    assert res.status_code == 400, res.text
    detail = res.json()["detail"]
    assert "Windows path" in detail
    assert "/workspace/C:" not in detail


def test_quoted_posix_path_still_works(tmp_path):
    video = tmp_path / "talk.mp4"
    video.write_bytes(b"x")
    assert normalize_user_path(f'"{video}"') == video
