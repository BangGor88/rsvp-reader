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

# Upgrade to the CUDA-enabled llama-cpp-python wheel when an Nvidia GPU is
# present on the build machine.  This embeds GPU support into the EXE so that
# end-users with Nvidia GPUs benefit from hardware acceleration automatically.
# Falls back silently to the already-installed CPU build if detection fails.
$nvidiaPresent = $false
try {
  $null = & nvidia-smi --query-gpu=name --format=csv,noheader 2>$null
  $nvidiaPresent = ($LASTEXITCODE -eq 0)
} catch {}

if ($nvidiaPresent) {
  # Detect installed CUDA major version (e.g. "12.4" → "cu124").
  $cudaTag = 'cu124'  # sensible default
  try {
    $nvOut = & nvidia-smi 2>$null | Out-String
    if ($nvOut -match 'CUDA Version:\s*(\d+)\.(\d+)') {
      $cudaTag = "cu$($Matches[1])$($Matches[2].PadLeft(1,'0'))"
    }
  } catch {}

  $wheelIndex = "https://abetlen.github.io/llama-cpp-python/whl/$cudaTag"
  Write-Host "[3/6] Nvidia GPU detected - installing CUDA llama-cpp-python ($cudaTag)..."
  try {
    & '.venv-build\Scripts\python.exe' -m pip install llama-cpp-python `
        --extra-index-url $wheelIndex `
        --force-reinstall `
        --no-cache-dir
    Write-Host "[3/6] CUDA-enabled llama-cpp-python installed ($cudaTag)."
  } catch {
    Write-Warning "CUDA wheel install failed; the EXE will use the CPU build."
  }
} else {
  Write-Host '[3/6] No Nvidia GPU detected - using CPU-only llama-cpp-python.'
}

Write-Host '[4/6] Building one-file executable...'
& '.venv-build\Scripts\python.exe' -m PyInstaller RSVPReader.spec --noconfirm --clean

Write-Host '[5/6] Standalone runtime prepared.'
Write-Host 'Runtime data will be stored under %LOCALAPPDATA%\RSVPReader when the EXE runs.'

Write-Host '[6/6] Build complete.'
Write-Host 'Output: dist\RSVPReader.exe'
