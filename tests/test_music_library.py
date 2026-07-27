from pathlib import Path

from reelwrite.edit.edl import Segment
from reelwrite.models.project import AudioSettings, Project
from reelwrite.models.source import Source
from reelwrite.models.word import Word
from reelwrite.music.catalog import load_catalog, public_track, track_by_id
from reelwrite.music.library import download_track, list_library, local_path_for
from reelwrite.render.ffmpeg import _build_export_filter, _required_source_ids
from reelwrite.render.music_filters import apply_music_bed


def test_catalog_loads_curated_tracks():
    data = load_catalog()
    assert len(data["tracks"]) >= 8
    track = track_by_id(data["tracks"][0]["id"])
    assert track and track["download_url"]
    public = public_track(track, downloaded=False)
    assert "download_url" not in public
    assert public["title"]


def test_apply_music_bed_mixes_with_gain():
    parts: list[str] = []
    label = apply_music_bed(parts, "[basea]", 1, 4.5, -18.0, False)
    graph = ";".join(parts)
    assert label == "[outa]"
    assert "aloop=loop=-1" in graph
    assert "volume=-18dB" in graph
    assert "amix=inputs=2" in graph
    assert "sidechaincompress" not in graph


def test_apply_music_bed_ducks_under_speech():
    parts: list[str] = []
    apply_music_bed(parts, "[basea]", 2, 3.0, -12.5, True)
    graph = ";".join(parts)
    assert "asplit=2[spmain][spsc]" in graph
    assert "sidechaincompress=" in graph
    assert "[spmain][mduck]amix=" in graph


def test_export_filter_includes_music_bed(tmp_path: Path):
    music = tmp_path / "bed.mp3"
    music.write_bytes(b"\x00" * 8)
    project = Project(
        sources=[
            Source(id="narr", path=str(tmp_path / "narr.mp4"), duration_s=8.0, has_audio=True),
            Source(
                id="bed",
                path=str(music),
                role="music",
                duration_s=30.0,
                has_audio=True,
            ),
        ],
        words=[
            Word(id=0, text="hello", start_s=0.1, end_s=0.4, source_id="narr"),
            Word(id=1, text="world", start_s=1.0, end_s=1.3, source_id="narr"),
        ],
        audio=AudioSettings(
            music_track_id="bed",
            music_gain_db=-16.0,
            duck_under_speech=True,
        ),
    )
    edl = [Segment("narr", 0.1, 0.4), Segment("narr", 1.0, 1.3)]
    source_ids = _required_source_ids(project, edl, "narr", include_assembly=False)
    assert source_ids == ["narr", "bed"]
    source_inputs = {sid: i for i, sid in enumerate(source_ids)}
    sources = {s.id: s for s in project.sources}
    from reelwrite.edit.timeline import Timeline

    vf = _build_export_filter(
        edl,
        project,
        Timeline(edl),
        str(tmp_path / "c.ass"),
        source_inputs,
        sources,
        include_assembly=False,
    )
    assert "volume=-16dB" in vf
    assert "sidechaincompress=" in vf
    assert "[outa]" in vf


def test_download_track_writes_library(monkeypatch, tmp_path: Path):
    catalog = load_catalog()["tracks"][0]
    track_id = catalog["id"]
    payload = b"ID3" + b"\x00" * 2048

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def raise_for_status(self):
            return None

        def iter_bytes(self, _size=65536):
            yield payload

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def stream(self, method, url):
            assert method == "GET"
            assert url == catalog["download_url"]
            return FakeResp()

        def close(self):
            return None

    monkeypatch.setenv("REELWRITE_DATA", str(tmp_path))
    monkeypatch.setattr("reelwrite.music.library.httpx.Client", FakeClient)

    item = download_track(track_id)
    assert item["downloaded"] is True
    path = Path(item["path"])
    assert path.is_file() and path.stat().st_size > 1000
    assert local_path_for(track_id) == path
    lib = list_library()
    assert any(t["id"] == track_id for t in lib)
