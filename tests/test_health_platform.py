"""Health/platform metadata keeps the Windows shell off a foreign API."""

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from reelwrite import __version__
from reelwrite.api.app import app
from reelwrite.paths import normalize_user_path


def _load_launcher():
    path = Path(__file__).resolve().parents[1] / "packaging" / "windows" / "launcher.py"
    spec = importlib.util.spec_from_file_location("reelwrite_launcher", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_health_reports_platform_and_version():
    body = TestClient(app).get("/health").json()
    assert body["ok"] is True
    assert body["platform"] == sys.platform
    assert body["version"] == __version__
    assert "frozen" in body


def test_fs_capabilities_native_pick_matches_platform():
    body = TestClient(app).get("/fs/capabilities").json()
    assert body["platform"] == sys.platform
    assert body["native_pick"] is (sys.platform == "win32")


def test_launcher_rejects_linux_api_on_windows(monkeypatch):
    mod = _load_launcher()
    monkeypatch.setattr(mod.sys, "platform", "win32")
    assert mod._api_platform_ok({"ok": True, "platform": "linux"}) is False
    assert mod._api_platform_ok({"ok": True, "platform": "win32"}) is True
    assert mod._api_platform_ok({"ok": True}) is True  # legacy


def test_windows_path_error_names_platform():
    if sys.platform == "win32":
        pytest.skip("POSIX-only assertion")
    with pytest.raises(ValueError, match=r"Windows path cannot be used.*linux"):
        normalize_user_path(r"C:\Users\tomso\Videos\clip.mp4")
