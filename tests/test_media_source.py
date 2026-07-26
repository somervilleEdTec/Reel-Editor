from pathlib import Path

from fastapi.testclient import TestClient

from reelwright.api.app import app
from reelwright.models.project import Project
from reelwright.models.source import Source
from reelwright.models.word import Word


def test_media_source_serves_project_video(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path / "data"))
    monkeypatch.setenv("REELWRIGHT_ROOT", str(tmp_path))
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    proj = tmp_path / "p.json"
    Project(
        sources=[Source(id="s", path=str(video))],
        words=[Word(id=0, text="Hi", start_s=0, end_s=0.2, source_id="s")],
    ).save(str(proj))
    c = TestClient(app)
    assert c.post("/project/open", json={"path": str(proj)}).status_code == 200
    res = c.get("/media/source")
    assert res.status_code == 200
    assert res.content.startswith(b"\x00\x00\x00\x18ftyp")
    assert "video" in (res.headers.get("content-type") or "")


def test_media_source_selects_source_by_id(tmp_path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_ROOT", str(tmp_path))
    first, second = tmp_path / "first.mp4", tmp_path / "second.mp4"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    project_path = tmp_path / "p.json"
    Project(
        sources=[
            Source(id="first", path=str(first)),
            Source(id="second", path=str(second)),
        ]
    ).save(str(project_path))
    client = TestClient(app)
    client.post("/project/open", json={"path": str(project_path)})
    response = client.get("/media/source", params={"id": "second"})
    assert response.status_code == 200
    assert response.content == b"second"
