$ErrorActionPreference = 'Stop'

Write-Host '[1/4] Building executable...'
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1

$exePath = Join-Path $PWD 'dist\RSVPReader.exe'
if (-not (Test-Path $exePath)) {
  throw 'Build output missing: dist\\RSVPReader.exe'
}

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$version = "RSVPReader-$timestamp"
$releaseDir = Join-Path $PWD ("release\\" + $version)

Write-Host '[2/4] Preparing release folder...'
New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
Copy-Item $exePath (Join-Path $releaseDir "$version.exe") -Force

Write-Host '[3/4] Writing SHA256 checksum...'
$hash = Get-FileHash (Join-Path $releaseDir "$version.exe") -Algorithm SHA256
"$($hash.Hash)  $version.exe" | Out-File -FilePath (Join-Path $releaseDir "$version.sha256.txt") -Encoding ascii -NoNewline

Write-Host '[4/4] Writing release notes...'
@(
  'RSVP Reader Windows Release',
  "Version: $version",
  "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
  '',
  'Run:',
  "  .\\$version.exe"
) | Out-File -FilePath (Join-Path $releaseDir 'RELEASE_NOTES.txt') -Encoding ascii

Write-Host "Release created: $releaseDir"
