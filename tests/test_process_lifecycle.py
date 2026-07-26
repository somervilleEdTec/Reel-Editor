from pathlib import Path

from reelwright import process_lifecycle as lifecycle
from reelwright.pid_file import clear_pid_file, pid_file_path, read_pid_file, write_pid_file
from reelwright.process_scan import ProcessInfo


def test_pid_file_write_read_clear(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path))
    assert read_pid_file() is None

    path = write_pid_file(4242)
    assert path == pid_file_path() == tmp_path / "reelwright.pid"
    assert read_pid_file() == 4242

    clear_pid_file()
    assert not path.exists()
    assert read_pid_file() is None
    clear_pid_file()  # idempotent


def test_read_pid_file_ignores_garbage(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path))
    pid_file_path().write_text("not-a-pid", encoding="utf-8")
    assert read_pid_file() is None
    pid_file_path().write_text("0", encoding="utf-8")
    assert read_pid_file() is None


def test_named_pid_files_are_separate(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path))
    write_pid_file(11)
    write_pid_file(22, "api")
    assert read_pid_file() == 11
    assert read_pid_file("api") == 22
    clear_pid_file("api")
    assert read_pid_file() == 11


def _proc(pid: int, name: str, exe: str = "", cmdline: str = "") -> ProcessInfo:
    return ProcessInfo(pid=pid, name=name, exe=exe or name, cmdline=cmdline or name)


def test_kill_targets_app_and_install_scoped_ffmpeg(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path))
    install = tmp_path / "app"
    (install / "vendor").mkdir(parents=True)
    procs = [
        _proc(101, "Reelwright.exe", str(install / "Reelwright.exe")),
        _proc(102, "reelwright-api.exe", str(install / "reelwright-api.exe")),
        _proc(103, "ffmpeg.exe", str(install / "vendor" / "ffmpeg" / "ffmpeg.exe")),
        _proc(104, "ffmpeg.exe", "C:/Tools/ffmpeg.exe", "ffmpeg -i movie.mp4"),
        _proc(105, "explorer.exe", "C:/Windows/explorer.exe"),
    ]
    killed_pids = []
    monkeypatch.setattr(lifecycle, "list_processes", lambda: procs)
    monkeypatch.setattr(
        lifecycle, "terminate_process_tree", lambda pid, *a, **k: killed_pids.append(pid) or True
    )

    write_pid_file(99, "api")
    killed = lifecycle.kill_reelwright_processes(str(install))

    assert killed == [99, 101, 102, 103]
    assert killed_pids == killed
    assert read_pid_file("api") is None


def test_kill_is_a_noop_when_nothing_matches(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("REELWRIGHT_DATA", str(tmp_path))
    monkeypatch.setattr(lifecycle, "list_processes", list)
    monkeypatch.setattr(lifecycle, "terminate_process_tree", lambda pid, *a, **k: False)
    assert lifecycle.kill_reelwright_processes(str(tmp_path)) == []
