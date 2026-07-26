import sys
from pathlib import Path

from uvicorn.config import Config

from reelwright.paths import ensure_stdio


def test_ensure_stdio_restores_none_streams(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path))
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    log_path = ensure_stdio()
    assert log_path is not None
    assert sys.stdout is not None
    assert sys.stderr is not None
    assert hasattr(sys.stdout, "isatty")
    assert log_path.exists() or log_path.parent.exists()


def test_uvicorn_config_survives_restored_stdio(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path))
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    ensure_stdio()
    # Same crash path as packaged api_entry: Config.configure_logging()
    Config("reelwright.api.app:app", host="127.0.0.1", port=8767, use_colors=False)
