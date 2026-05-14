# Desktop Build and Release

## Build executable

Prerequisites on Windows:

- Node.js and npm
- A Python virtual environment at `.venv`
- Microsoft Visual C++ Build Tools with CMake support
- Expect the first build to take longer because `llama-cpp-python` may compile a native wheel

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

Produces:

- `dist\RSVPReader.exe`

Runtime behavior of the standalone EXE:

- Launches the FastAPI server locally on `127.0.0.1:8000`
- Opens the app automatically in the default browser
- Stores writable app data in `%LOCALAPPDATA%\RSVPReader`
- Uses `%LOCALAPPDATA%\RSVPReader\uploads` for uploaded books
- Uses `%LOCALAPPDATA%\RSVPReader\models` for GGUF models
- Shows the embedded build version in the app health bar and `/api/health`
- Shows a Windows startup error dialog if no GGUF model is found or `LLAMA_MODEL_PATH` points to a missing file
- Writes a startup and runtime log to `%LOCALAPPDATA%\RSVPReader\rsvpreader.log`

## GGUF model setup

The translation and chat features require a GGUF model file:

1. Place any `.gguf` model file in `%LOCALAPPDATA%\RSVPReader\models\`
2. The app auto-discovers the first `.gguf` found in that folder on startup
3. Use the **Open Models Folder** button on the upload page to open that folder in Explorer

The `llama_cpp` native DLLs (`llama.dll`, `ggml.dll`, etc.) are bundled inside the EXE
automatically by `RSVPReader.spec` — no separate DLL installation is required.

## Logging

All startup info and runtime errors from the EXE are written to:

```
%LOCALAPPDATA%\RSVPReader\rsvpreader.log
```

Inspect this file when diagnosing crashes or unexpected behavior.

## Create release artifact

```powershell
powershell -ExecutionPolicy Bypass -File scripts\release_exe.ps1
```

Creates:

- `release\RSVPReader-<timestamp>\<version>.exe`
- `release\RSVPReader-<timestamp>\<version>.sha256.txt`
- `release\RSVPReader-<timestamp>\RELEASE_NOTES.txt`

`release_exe.ps1` now injects the release version into the packaged EXE so the standalone Windows app shows the correct build even without the repository `release\` folder present.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\release_exe.ps1
```

Creates:

- `release\RSVPReader-<timestamp>\<version>.exe`
- `release\RSVPReader-<timestamp>\<version>.sha256.txt`
- `release\RSVPReader-<timestamp>\RELEASE_NOTES.txt`

`release_exe.ps1` now injects the release version into the packaged EXE so the standalone Windows app shows the correct build even without the repository `release\` folder present.