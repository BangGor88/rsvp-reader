$ErrorActionPreference = 'Stop'

$buildVersion = if ($env:RSVP_BUILD_VERSION) { $env:RSVP_BUILD_VERSION } else { "RSVPReader-dev-$(Get-Date -Format 'yyyyMMdd-HHmmss')" }
$buildVersionFile = Join-Path $PWD 'backend\build_version.txt'

Write-Host "[0/6] Writing build version: $buildVersion"
$buildVersion | Out-File -FilePath $buildVersionFile -Encoding ascii -NoNewline

Write-Host '[1/6] Building frontend assets...'
Push-Location frontend
npm install
npm run build
Pop-Location

Write-Host '[2/6] Copying frontend assets into backend/static...'
$staticDir = Join-Path $PWD 'backend\static'
if (Test-Path $staticDir) {
  Remove-Item $staticDir -Recurse -Force
}
New-Item -ItemType Directory -Path $staticDir | Out-Null
Copy-Item -Path 'frontend\dist\*' -Destination $staticDir -Recurse -Force

Write-Host '[3/6] Installing PyInstaller...'
if (-not (Test-Path '.venv-build\Scripts\python.exe')) {
  & '.venv/Scripts/python.exe' -m venv .venv-build
}

& '.venv-build\Scripts\python.exe' -m pip install --upgrade pip
& '.venv-build\Scripts\python.exe' -m pip install -r backend/requirements.txt
& '.venv-build\Scripts\python.exe' -m pip install pyinstaller

Write-Host '[4/6] Building one-file executable...'
& '.venv-build\Scripts\python.exe' -m PyInstaller RSVPReader.spec --noconfirm --clean

Write-Host '[5/6] Standalone runtime prepared.'
Write-Host 'Runtime data will be stored under %LOCALAPPDATA%\RSVPReader when the EXE runs.'

Write-Host '[6/6] Build complete.'
Write-Host 'Output: dist\RSVPReader.exe'
