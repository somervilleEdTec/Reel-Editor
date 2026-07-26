# Stop Reelwright processes so the uninstaller can delete files in use.
# Usage: powershell -ExecutionPolicy Bypass -File uninstall_kill.ps1 -InstallDir "C:\path\to\Reelwright"
# Always exits 0: nothing running is a success for uninstall.

param(
  [string]$InstallDir = $PSScriptRoot
)

$ErrorActionPreference = "SilentlyContinue"

function Stop-Tree([int]$ProcessId) {
  if ($ProcessId -le 0) { return }
  & taskkill.exe /F /T /PID $ProcessId 2>&1 | Out-Null
  if (Get-Process -Id $ProcessId) {
    Stop-Process -Id $ProcessId -Force
  }
}

$pidFile = Join-Path $env:LOCALAPPDATA "Reelwright\reelwright.pid"
$apiPidFile = Join-Path $env:LOCALAPPDATA "Reelwright\api.pid"
foreach ($file in @($pidFile, $apiPidFile)) {
  if (Test-Path $file) {
    $raw = Get-Content $file -Raw
    $recorded = 0
    if ($raw -and [int]::TryParse($raw.Trim(), [ref]$recorded)) {
      Stop-Tree $recorded
    }
    Remove-Item $file -Force
  }
}

foreach ($name in @("Reelwright", "reelwright-api")) {
  foreach ($proc in (Get-Process -Name $name)) {
    Stop-Tree $proc.Id
  }
}

# Only vendored/spawned media tools from this install, never a system-wide ffmpeg.
$root = (Resolve-Path $InstallDir).Path
if ($root) {
  foreach ($proc in (Get-Process -Name "ffmpeg", "ffprobe")) {
    if ($proc.Path -and $proc.Path.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
      Stop-Tree $proc.Id
    }
  }
}

exit 0
