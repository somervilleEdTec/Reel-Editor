"""Filesystem places, resolve, and video-picker path guards."""

from pathlib import Path

from fastapi.testclient import TestClient

from reelwrite.api.app import app
from reelwrite.api.fs_access import is_allowed, list_places


def test_fs_places_includes_home_and_projects(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRITE_DATA", str(tmp_path / "data"))
    projects = tmp_path / "projects"
    projects.mkdir()
    c = TestClient(app)
    assert c.post("/setup/projects-dir", json={"path": str(projects)}).status_code == 200
    body = c.get("/fs/places").json()
    ids = {p["id"] for p in body["places"]}
    assert "home" in ids
    assert "projects" in ids
    projects_place = next(p for p in body["places"] if p["id"] == "projects")
    assert Path(projects_place["path"]) == projects.resolve()


def test_fs_resolve_file_and_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRITE_DATA", str(tmp_path / "data"))
    monkeypatch.setenv("REELWRITE_FS_ROOTS", str(tmp_path))
    media = tmp_path / "media"
    media.mkdir()
    video = media / "talk.mp4"
    video.write_bytes(b"x")
    c = TestClient(app)
    c.post("/setup/projects-dir", json={"path": str(tmp_path / "projects")})

    dir_res = c.post("/fs/resolve", json={"path": str(media)})
    assert dir_res.status_code == 200
    assert dir_res.json()["kind"] == "dir"

    file_res = c.post("/fs/resolve", json={"path": f'"{video}"'})
    assert file_res.status_code == 200
    assert file_res.json()["kind"] == "file"
    assert file_res.json()["path"] == str(video.resolve())

    missing = c.post("/fs/resolve", json={"path": str(media / "nope.mp4")})
    assert missing.status_code == 200
    assert missing.json()["ok"] is False
    assert missing.json()["kind"] == "missing"


def test_fs_list_parent_when_projects_outside_home(tmp_path, monkeypatch):
    """Projects under /tmp used to trap the picker with parent=None."""
    monkeypatch.setenv("REELWRITE_DATA", str(tmp_path / "data"))
    monkeypatch.setenv("REELWRITE_FS_ROOTS", str(tmp_path))
    projects = tmp_path / "projects"
    projects.mkdir()
    (tmp_path / "Videos").mkdir()
    c = TestClient(app)
    c.post("/setup/projects-dir", json={"path": str(projects)})
    res = c.get("/fs/list", params={"dir": str(projects)})
    assert res.status_code == 200
    parent = res.json()["parent"]
    assert parent is not None
    assert Path(parent) == tmp_path.resolve()


def test_create_rejects_selection_label(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRITE_DATA", str(tmp_path / "data"))
    projects = tmp_path / "projects"
    projects.mkdir()
    c = TestClient(app)
    c.post("/setup/projects-dir", json={"path": str(projects)})
    res = c.post("/projects/create", json={"video_path": "2 files selected"})
    assert res.status_code == 400
    assert "full file path" in res.json()["detail"].lower()


def test_mount_roots_are_allowed(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRITE_DATA", str(tmp_path / "data"))
    monkeypatch.setenv("REELWRITE_FS_ROOTS", str(tmp_path))
    media = tmp_path / "ext-drive"
    media.mkdir()
    assert is_allowed(media)
    places = list_places()
    assert any(p["path"] == str(Path.home().resolve()) for p in places)
