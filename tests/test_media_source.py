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
