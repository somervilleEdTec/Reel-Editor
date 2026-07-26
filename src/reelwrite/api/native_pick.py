"""Native OS file/folder dialogs (Windows WinForms via PowerShell)."""

from __future__ import annotations

import subprocess
import sys

from reelwrite.media_formats import VIDEO_EXTS


def pick_paths(*, allow_dirs: bool = False, multiple: bool = False) -> list[str]:
    """Show a native picker and return selected absolute paths (may be empty)."""
    if sys.platform != "win32":
        raise RuntimeError("Native picker is only available on Windows")
    if allow_dirs:
        return _pick_folder()
    return _pick_files(multiple=multiple)


def _pick_files(*, multiple: bool) -> list[str]:
    exts = ";".join(f"*{ext}" for ext in sorted(VIDEO_EXTS))
    multi = "$true" if multiple else "$false"
    script = f"""
Add-Type -AssemblyName System.Windows.Forms
$d = New-Object System.Windows.Forms.OpenFileDialog
$d.Title = 'Choose video'
$d.Filter = 'Video files|{exts}|All files|*.*'
$d.Multiselect = {multi}
$d.CheckFileExists = $true
if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {{
  if ($d.Multiselect) {{ $d.FileNames | ForEach-Object {{ $_ }} }}
  else {{ $d.FileName }}
}}
"""
    return _run_ps(script)


def _pick_folder() -> list[str]:
    script = """
Add-Type -AssemblyName System.Windows.Forms
$d = New-Object System.Windows.Forms.FolderBrowserDialog
$d.Description = 'Choose folder'
if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
  $d.SelectedPath
}
"""
    return _run_ps(script)


def _run_ps(script: str) -> list[str]:
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-STA",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"Could not open system file picker: {exc}") from exc
    if result.returncode not in (0, None) and not result.stdout.strip():
        err = (result.stderr or result.stdout or "picker failed").strip()
        raise RuntimeError(err)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]
