from fastapi.testclient import TestClient

from reelwright.api.app import app
from reelwright.models.project import Project
from reelwright.models.source import Source
from reelwright.models.word import Word


def _open(tmp_path, words):
    path = tmp_path / "project.json"
    Project(
        sources=[Source(id="narr", path=str(tmp_path / "narr.mp4"), duration_s=10)],
        words=words,
    ).save(str(path))
    client = TestClient(app)
    assert client.post("/project/open", json={"path": str(path)}).status_code == 200
    return client


def test_words_range_and_cleanup(tmp_path):
    words = [
        Word(id=0, text="Um,", start_s=0, end_s=0.2, source_id="narr"),
        Word(id=1, text="hello", start_s=0.3, end_s=0.5, source_id="narr"),
        Word(id=2, text="you", start_s=0.6, end_s=0.7, source_id="narr"),
        Word(id=3, text="know", start_s=0.8, end_s=0.9, source_id="narr"),
    ]
    client = _open(tmp_path, words)
    result = client.post(
        "/words/range", json={"start_s": 0.25, "end_s": 0.55, "deleted": True}
    )
    assert result.json()["changed"] == 1
    assert client.post("/words/cleanup", json={}).json()["deleted"] == 3
    assert all(word["deleted"] for word in client.get("/project").json()["words"])


def test_undo_and_redo(tmp_path):
    client = _open(
        tmp_path, [Word(id=0, text="hello", start_s=0, end_s=0.2, source_id="narr")]
    )
    client.post("/words/delete", json={"word_id": 0, "deleted": True})
    assert client.post("/project/undo").json()["words"][0]["deleted"] is False
    assert client.post("/project/redo").json()["words"][0]["deleted"] is True


def test_edl_endpoint(tmp_path):
    client = _open(
        tmp_path,
        [
            Word(id=0, text="hello", start_s=0.1, end_s=0.4, source_id="narr"),
            Word(id=1, text="world", start_s=0.5, end_s=0.9, source_id="narr"),
        ],
    )
    result = client.get("/edl")
    assert result.status_code == 200
    assert len(result.json()["segments"]) == 1
    assert result.json()["output_duration_s"] > 0
    seg = result.json()["segments"][0]
    assert "output_start" in seg and "source_start" in seg
    assert result.json()["total_duration"] == result.json()["output_duration_s"]


def test_markers_get_and_post(tmp_path):
    client = _open(tmp_path, [])
    assert client.get("/markers").json()["markers"] == []
    created = client.post("/markers", json={"t_out_s": 1.5, "label": "beat"})
    assert created.status_code == 200
    assert created.json()["markers"][0]["t_out_s"] == 1.5
    assert client.get("/markers").json()["markers"][0]["label"] == "beat"


def test_export_settings_transition(tmp_path):
    client = _open(tmp_path, [])
    result = client.post(
        "/export-settings",
        json={"transition": "crossfade", "transition_s": 0.4},
    )
    assert result.status_code == 200
    assert result.json()["transition"] == "crossfade"
    assert client.get("/project").json()["export"]["transition_s"] == 0.4


def test_assembly_import_and_reorder(tmp_path, monkeypatch):
    paths = [tmp_path / "one.mp4", tmp_path / "two.mp4"]
    for path in paths:
        path.write_bytes(b"video")

    def fake_probe(path, source_id, role):
        return Source(id=source_id, path=path, role=role, duration_s=2)

    monkeypatch.setattr("reelwright.api.source_ops.probe", fake_probe)
    client = _open(
        tmp_path,
        [Word(id=i, text="word", start_s=i, end_s=i + 0.5, source_id="narr")
         for i in range(4)],
    )
    result = client.post("/assembly/import", json={"paths": [str(p) for p in paths]})
    assert result.status_code == 200
    clips = client.post("/assembly/distribute").json()["clips"]
    reordered = client.post(
        "/assembly/reorder", json={"order": [clips[1]["id"], clips[0]["id"]]}
    )
    assert [clip["id"] for clip in reordered.json()["clips"]] == [
        clips[1]["id"], clips[0]["id"]
    ]


def test_sources_accept_single_path_and_id(tmp_path, monkeypatch):
    media = tmp_path / "media.mp4"
    media.write_bytes(b"video")

    def fake_probe(path, source_id, role):
        return Source(id=source_id, path=path, role=role, duration_s=2)

    monkeypatch.setattr("reelwright.api.source_ops.probe", fake_probe)
    client = _open(tmp_path, [])
    added = client.post("/sources/add", json={"path": str(media)})
    assert added.status_code == 200
    source_id = next(s["id"] for s in added.json()["sources"] if s["id"] != "narr")
    removed = client.post("/sources/remove", json={"id": source_id})
    assert all(source["id"] != source_id for source in removed.json()["sources"])


def test_thumb_rejects_outside_allowlist(monkeypatch, tmp_path):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path / "data"))
    response = TestClient(app).get("/fs/thumb", params={"path": "/etc/passwd"})
    assert response.status_code == 403
