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

function Test-OwnedPid([int]$ProcessId, [string]$Root) {
  $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId"
  if (-not $proc) { return $false }
  $name = [IO.Path]::GetFileNameWithoutExtension($proc.Name)
  if ($name -notin @("Reelwright", "reelwright-api")) { return $false }
  if (-not $proc.ExecutablePath) { return $true }
  $exe = $proc.ExecutablePath
  $prefix = $Root.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
  return $exe.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)
}

$root = $null
try { $root = (Resolve-Path $InstallDir).Path } catch { $root = $InstallDir }

$pidFile = Join-Path $env:LOCALAPPDATA "Reelwright\reelwright.pid"
$apiPidFile = Join-Path $env:LOCALAPPDATA "Reelwright\api.pid"
foreach ($file in @($pidFile, $apiPidFile)) {
  if (Test-Path $file) {
    $raw = Get-Content $file -Raw
    $recorded = 0
    if ($raw -and [int]::TryParse($raw.Trim(), [ref]$recorded)) {
      if ($root -and (Test-OwnedPid $recorded $root)) {
        Stop-Tree $recorded
      }
    }
    Remove-Item $file -Force
  }
}

if ($root) {
  $prefix = $root.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
  foreach ($name in @("Reelwright", "reelwright-api")) {
    foreach ($proc in (Get-Process -Name $name)) {
      if ($proc.Path -and $proc.Path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        Stop-Tree $proc.Id
      }
    }
  }
  foreach ($proc in (Get-Process -Name "ffmpeg", "ffprobe")) {
    if ($proc.Path -and $proc.Path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
      Stop-Tree $proc.Id
    }
  }
}

exit 0
