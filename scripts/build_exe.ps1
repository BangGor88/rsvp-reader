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

# Legacy mode (opt-in) builds llama-cpp-python from source with conservative
# CPU flags for wider compatibility on older Windows PCs that crash with
# 0xc000001d (illegal instruction).
# Usage:
#   $env:RSVP_LLAMA_LEGACY = "1"
#   .\scripts\build_exe.ps1
$legacyLlamaBuild = ($env:RSVP_LLAMA_LEGACY -eq '1')

if ($legacyLlamaBuild) {
  # Older llama-cpp-python versions can run on CPUs that still throw
  # 0xc000001d with recent releases, even with AVX disabled.
  $legacyLlamaVersion = $env:RSVP_LLAMA_LEGACY_VERSION
  if ($legacyLlamaVersion) {
    Write-Host "[3/6] RSVP_LLAMA_LEGACY=1 - building llama-cpp-python==$legacyLlamaVersion from source (max compatibility)..."
  } else {
    Write-Host "[3/6] RSVP_LLAMA_LEGACY=1 - rebuilding current llama-cpp-python from source (max compatibility)..."
  }
  $oldCmakeArgs = $env:CMAKE_ARGS
  $oldTmp = $env:TMP
  $oldTemp = $env:TEMP
  $legacyTmp = Join-Path $PWD '.build-tmp\legacy-llama'
  New-Item -ItemType Directory -Path $legacyTmp -Force | Out-Null

  $env:CMAKE_ARGS = '-DGGML_NATIVE=OFF -DGGML_CPU_ALL_VARIANTS=OFF -DGGML_AVX=OFF -DGGML_AVX2=OFF -DGGML_FMA=OFF -DGGML_F16C=OFF -DGGML_OPENMP=OFF -DGGML_BLAS=OFF -DGGML_CUDA=OFF -DGGML_METAL=OFF -DGGML_VULKAN=OFF -DCMAKE_C_FLAGS=/arch:SSE2 -DCMAKE_CXX_FLAGS=/arch:SSE2'
  $env:TMP = $legacyTmp
  $env:TEMP = $legacyTmp

  try {
    & '.venv-build\Scripts\python.exe' -m pip install "cmake>=3.21" ninja "scikit-build-core>=0.10"
    if ($LASTEXITCODE -ne 0) {
      throw 'Failed to install legacy build prerequisites (cmake/ninja/scikit-build-core).'
    }

    & '.venv-build\Scripts\python.exe' -m pip uninstall -y llama-cpp-python
    if ($legacyLlamaVersion) {
      & '.venv-build\Scripts\python.exe' -m pip install "llama-cpp-python==$legacyLlamaVersion" `
        --force-reinstall `
        --no-binary llama-cpp-python `
        --no-build-isolation `
        --no-cache-dir
      if ($LASTEXITCODE -ne 0) {
        throw "Legacy install failed for llama-cpp-python==$legacyLlamaVersion"
      }
      Write-Host "[3/6] Legacy llama-cpp-python build completed (version $legacyLlamaVersion)."
    } else {
      & '.venv-build\Scripts\python.exe' -m pip install llama-cpp-python `
        --force-reinstall `
        --no-binary llama-cpp-python `
        --no-build-isolation `
        --no-cache-dir
      if ($LASTEXITCODE -ne 0) {
        throw 'Legacy source reinstall failed for llama-cpp-python (current version).'
      }
      Write-Host '[3/6] Legacy llama-cpp-python source rebuild completed (current version).'
    }

    & '.venv-build\Scripts\python.exe' -m pip show llama-cpp-python | Out-Null
    if ($LASTEXITCODE -ne 0) {
      throw 'llama-cpp-python is not installed after legacy build step.'
    }
  } finally {
    if ($null -eq $oldCmakeArgs) {
      Remove-Item Env:\CMAKE_ARGS -ErrorAction SilentlyContinue
    } else {
      $env:CMAKE_ARGS = $oldCmakeArgs
    }

    if ($null -eq $oldTmp) {
      Remove-Item Env:\TMP -ErrorAction SilentlyContinue
    } else {
      $env:TMP = $oldTmp
    }

    if ($null -eq $oldTemp) {
      Remove-Item Env:\TEMP -ErrorAction SilentlyContinue
    } else {
      $env:TEMP = $oldTemp
    }
  }
}

# CUDA wheel install is opt-in. CPU-only build is the default for maximum
# compatibility across target PCs. To opt into a CUDA build, set:
#   $env:RSVP_ENABLE_CUDA_BUILD = "1"
# before running this script.
$nvidiaPresent = $false
try {
  $null = & nvidia-smi --query-gpu=name --format=csv,noheader 2>$null
  $nvidiaPresent = ($LASTEXITCODE -eq 0)
} catch {}

$enableCudaBuild = ($env:RSVP_ENABLE_CUDA_BUILD -eq '1')

if ($legacyLlamaBuild) {
  Write-Host '[3/6] Skipping CUDA wheel because RSVP_LLAMA_LEGACY=1 is enabled.'
} elseif ($enableCudaBuild -and $nvidiaPresent) {
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
} elseif ($enableCudaBuild -and -not $nvidiaPresent) {
  Write-Warning '[3/6] RSVP_ENABLE_CUDA_BUILD=1 but no Nvidia GPU was detected on this build machine. Using CPU-only llama-cpp-python.'
} else {
  Write-Host '[3/6] Building CPU-only llama-cpp-python for maximum compatibility.'
}

Write-Host '[4/6] Building one-file executable...'
& '.venv-build\Scripts\python.exe' -m PyInstaller RSVPReader.spec --noconfirm --clean

Write-Host '[5/6] Standalone runtime prepared.'
Write-Host 'Runtime data will be stored under %LOCALAPPDATA%\RSVPReader when the EXE runs.'

Write-Host '[6/6] Build complete.'
Write-Host 'Output: dist\RSVPReader.exe'
