# Download a Windows FFmpeg essentials build into vendor/ffmpeg (not committed).
# Usage: powershell -File packaging/windows/fetch_ffmpeg.ps1 [-DestDir path]

param(
  [string]$DestDir = ""
)

$ErrorActionPreference = "Stop"
if (-not $DestDir) {
  $DestDir = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")) "vendor\ffmpeg"
}

New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
$tmp = Join-Path $env:TEMP ("ffmpeg-essentials-" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $tmp | Out-Null

try {
  $zip = Join-Path $tmp "ffmpeg.zip"
  $url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
  Write-Host "Downloading $url"
  Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
  Expand-Archive -Path $zip -DestinationPath $tmp -Force
  $ffmpeg = Get-ChildItem -Path $tmp -Recurse -Filter ffmpeg.exe | Select-Object -First 1
  $ffprobe = Get-ChildItem -Path $tmp -Recurse -Filter ffprobe.exe | Select-Object -First 1
  if (-not $ffmpeg -or -not $ffprobe) {
    throw "ffmpeg.exe / ffprobe.exe not found in archive"
  }
  Copy-Item $ffmpeg.FullName (Join-Path $DestDir "ffmpeg.exe") -Force
  Copy-Item $ffprobe.FullName (Join-Path $DestDir "ffprobe.exe") -Force
  Write-Host "Installed to $DestDir"
}
finally {
  Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
}
