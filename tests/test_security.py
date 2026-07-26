from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from reelwrite.api.app import app
from reelwrite.captions.ass import render_ass
from reelwrite.edit.edl import Segment
from reelwrite.edit.timeline import Timeline
from reelwrite.models.project import Project
from reelwrite.models.source import Source
from reelwrite.models.word import Word
from reelwrite.security.egress import assert_azure_openai_endpoint
from reelwrite.security.paths import PathDenied, resolve_workspace_path


def test_cors_rejects_foreign_origin():
    c = TestClient(app)
    r = c.get("/health", headers={"Origin": "https://evil.example"})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") is None


def test_cors_allows_localhost():
    c = TestClient(app)
    r = c.get("/health", headers={"Origin": "http://127.0.0.1:8765"})
    assert r.headers.get("access-control-allow-origin") == "http://127.0.0.1:8765"


def test_open_rejects_system_path(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("REELWRITE_ROOT", str(tmp_path))
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/project/open", json={"path": "/etc/passwd"})
    assert r.status_code in (403, 404)


def test_open_rejects_path_outside_root(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("REELWRITE_ROOT", str(tmp_path))
    outside = Path("/tmp") / "reelwrite-outside-proj.json"
    Project(sources=[Source(id="s", path="x.mp4")]).save(str(outside))
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/project/open", json={"path": str(outside)})
    assert r.status_code == 403


def test_ass_escapes_override_codes(tmp_path: Path):
    project = Project(
        sources=[Source(id="s", path="x.mp4")],
        words=[Word(id=0, text=r"Hi{\an8}X", start_s=0.1, end_s=0.3, source_id="s")],
    )
    out = tmp_path / "c.ass"
    render_ass(project, Timeline([Segment("s", 0.0, 1.0)]), str(out))
    line = next(ln for ln in out.read_text().splitlines() if ln.startswith("Dialogue"))
    assert r"{\an8}" not in line.lower()
    assert "\\{" in line
    assert "HI" in line or "Hi" in line


def test_azure_endpoint_must_be_https_azure():
    with pytest.raises(ValueError):
        assert_azure_openai_endpoint("http://evil.example/openai")
    with pytest.raises(ValueError):
        assert_azure_openai_endpoint("https://evil.example")
    assert assert_azure_openai_endpoint(
        "https://myhub.openai.azure.com/"
    ) == "https://myhub.openai.azure.com"


def test_resolve_blocks_etc(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("REELWRITE_ROOT", str(tmp_path))
    with pytest.raises(PathDenied):
        resolve_workspace_path("/etc/passwd")
