$ErrorActionPreference = 'Stop'

Write-Host '[1/5] Building frontend assets...'
Push-Location frontend
npm install
npm run build
Pop-Location

Write-Host '[2/5] Copying frontend assets into backend/static...'
$staticDir = Join-Path $PWD 'backend\static'
if (Test-Path $staticDir) {
  Remove-Item $staticDir -Recurse -Force
}
New-Item -ItemType Directory -Path $staticDir | Out-Null
Copy-Item -Path 'frontend\dist\*' -Destination $staticDir -Recurse -Force

Write-Host '[3/5] Installing PyInstaller...'
if (-not (Test-Path '.venv-build\Scripts\python.exe')) {
  & '.venv/Scripts/python.exe' -m venv .venv-build
}

& '.venv-build\Scripts\python.exe' -m pip install --upgrade pip
& '.venv-build\Scripts\python.exe' -m pip install -r backend/requirements.txt
& '.venv-build\Scripts\python.exe' -m pip install pyinstaller

Write-Host '[4/5] Building one-file executable...'
& '.venv-build\Scripts\python.exe' -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --name RSVPReader `
  --add-data "backend/static;static" `
  --paths backend `
  backend/desktop_main.py

Write-Host '[5/5] Build complete.'
Write-Host 'Output: dist\RSVPReader.exe'
