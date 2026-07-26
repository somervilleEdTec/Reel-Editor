from fastapi.testclient import TestClient

from reelwright.api.app import app
from reelwright.models.project import Project
from reelwright.models.source import Source
from reelwright.models.word import Word


def test_setup_status(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path / "data"))
    c = TestClient(app)
    res = c.get("/setup/status")
    assert res.status_code == 200
    body = res.json()
    assert "ffmpeg" in body
    assert "projects_dir" in body


def test_setup_projects_dir_and_complete(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path / "data"))
    projects = tmp_path / "projects"
    projects.mkdir()
    c = TestClient(app)
    assert c.post("/setup/projects-dir", json={"path": str(projects)}).status_code == 200
    assert c.post("/setup/consent", json={"consented": True}).json()["ok"] is True
    # complete requires ffmpeg — skip assertion if missing in CI
    status = c.get("/setup/status").json()
    if status["ffmpeg"]["found"]:
        assert c.post("/setup/complete", json={}).status_code == 200
        assert c.get("/setup/status").json()["completed"] is True


def test_list_projects_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path / "data"))
    c = TestClient(app)
    c.post("/setup/projects-dir", json={"path": str(tmp_path / "projects")})
    data = c.get("/projects").json()
    assert data["projects"] == []


def test_fs_list_allowed(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path / "data"))
    monkeypatch.setenv("REELWRIGHT_FS_ROOTS", str(tmp_path))
    d = tmp_path / "media"
    d.mkdir()
    (d / "clip.mp4").write_bytes(b"x")
    c = TestClient(app)
    res = c.get("/fs/list", params={"dir": str(d)})
    assert res.status_code == 200
    names = {e["name"] for e in res.json()["entries"]}
    assert "clip.mp4" in names


def test_caption_presets():
    c = TestClient(app)
    data = c.get("/captions/presets").json()
    assert "sticker" in data


def test_project_open_for_editor(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path / "data"))
    p = Project(
        sources=[Source(id="s", path="x.mp4")],
        words=[Word(id=0, text="Hi", start_s=0, end_s=0.2, source_id="s")],
    )
    path = tmp_path / "p.json"
    p.save(str(path))
    c = TestClient(app)
    assert c.post("/project/open", json={"path": str(path)}).status_code == 200
    assert c.get("/project").status_code == 200
