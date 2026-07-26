from fastapi.testclient import TestClient

from reelwright.api.app import app
from reelwright.models.project import Project
from reelwright.models.source import Source
from reelwright.models.word import Word


def test_health():
    c = TestClient(app)
    assert c.get("/health").json()["ok"] is True


def test_delete_word(tmp_path):
    p = Project(
        sources=[Source(id="s", path="x.mp4")],
        words=[Word(id=0, text="Hi", start_s=0, end_s=0.2, source_id="s")],
    )
    path = tmp_path / "p.json"
    p.save(str(path))
    c = TestClient(app)
    assert c.post("/project/open", json={"path": str(path)}).status_code == 200
    assert c.post("/words/delete", json={"word_id": 0, "deleted": True}).status_code == 200
    data = c.get("/project").json()
    assert data["words"][0]["deleted"] is True


def test_safezone_hits():
    from reelwright.api.safezone import safezone_hits

    p = Project()
    p.captions.y = 0.95
    p.layers.inset.x = 0.9
    hits = safezone_hits(p)
    assert hits
