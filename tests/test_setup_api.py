from pathlib import Path

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
    entries = res.json()["entries"]
    names = {e["name"] for e in entries}
    assert "clip.mp4" in names
    clip = next(e for e in entries if e["name"] == "clip.mp4")
    assert clip["size"] == 1


def test_fs_list_includes_new_camera_extensions(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path / "data"))
    monkeypatch.setenv("REELWRIGHT_FS_ROOTS", str(tmp_path))
    d = tmp_path / "media"
    d.mkdir()
    for name in ("cam.MTS", "deck.m2ts", "old.wmv", "phone.3gp", "note.txt"):
        (d / name).write_bytes(b"x")
    c = TestClient(app)
    names = {e["name"] for e in c.get("/fs/list", params={"dir": str(d)}).json()["entries"]}
    assert {"cam.MTS", "deck.m2ts", "old.wmv", "phone.3gp"} <= names
    assert "note.txt" not in names


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


def test_create_project_accepts_copy_as_path_quotes(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path / "data"))
    projects = tmp_path / "projects"
    projects.mkdir()
    video = tmp_path / "talk.mp4"
    video.write_bytes(b"x")
    c = TestClient(app)
    assert c.post("/setup/projects-dir", json={"path": str(projects)}).status_code == 200
    # Windows Explorer "Copy as path" wraps in double quotes.
    res = c.post("/projects/create", json={"video_path": f'"{video}"'})
    assert res.status_code == 200, res.text
    body = res.json()
    assert str(projects) in body["path"]
    # Job may fail ffprobe on dummy bytes; path must be unquoted in the error/result.
    import time

    job = None
    for _ in range(40):
        job = c.get(f"/jobs/{body['job_id']}").json()
        if job["status"] in ("done", "error", "cancelled"):
            break
        time.sleep(0.05)
    assert job is not None
    blob = str(job.get("error") or job.get("result") or "")
    assert f'"{video}"' not in blob
    assert str(video) in blob or job["status"] == "done"



def test_create_project_accepts_new_extensions(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path / "data"))
    projects = tmp_path / "projects"
    projects.mkdir()
    video = tmp_path / "cam.MTS"
    video.write_bytes(b"x")
    c = TestClient(app)
    assert c.post("/setup/projects-dir", json={"path": str(projects)}).status_code == 200
    res = c.post("/projects/create", json={"video_path": str(video)})
    assert res.status_code == 200, res.text


def test_create_project_rejects_unknown_extension(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path / "data"))
    projects = tmp_path / "projects"
    projects.mkdir()
    doc = tmp_path / "notes.txt"
    doc.write_bytes(b"x")
    c = TestClient(app)
    c.post("/setup/projects-dir", json={"path": str(projects)})
    res = c.post("/projects/create", json={"video_path": str(doc)})
    assert res.status_code == 400
    assert "Unsupported video type" in res.json()["detail"]


def test_create_project_rejects_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path / "data"))
    projects = tmp_path / "projects"
    projects.mkdir()
    c = TestClient(app)
    c.post("/setup/projects-dir", json={"path": str(projects)})
    res = c.post("/projects/create", json={"video_path": str(tmp_path)})
    assert res.status_code == 400
    assert "folder" in res.json()["detail"].lower()
