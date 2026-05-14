# RSVP Reader 📖
![Platform](https://img.shields.io/badge/platform-Windows-blue?logo=windows)
![License](https://img.shields.io/badge/license-MIT-green)

![RSVP Reader](<Screenshot 2026-05-14 135056.png>)

Help your kiddos with reading a book in an ease way? Look no further 🔥 Here I made an exectuable file that can help reading a book 📖. Read PDFs at high speed, one word at a time. Upload, set your pace, and focus.⚡

## Current Build

- Current packaged build in this repository: `RSVPReader-20260406-184446`
- The running app now shows the current build in the top health bar.

## Get the Executable! 🧰⬇️

Download the Windows executable [here](dist/). But if you want to build it yourself follow the [quick start](#Quick-Start) below. 

## Windows Standalone App

The project can be packaged as a standalone Windows executable:

- Build output: `dist\RSVPReader.exe`
- The EXE launches the app locally on `http://127.0.0.1:8000`
- User data is stored in `%LOCALAPPDATA%\RSVPReader\`
- Uploaded books are stored under `%LOCALAPPDATA%\RSVPReader\uploads`
- GGUF models can be placed under `%LOCALAPPDATA%\RSVPReader\models`
- If no model is found, the app shows a Windows startup dialog with the required models path

To build the standalone EXE:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

Windows build prerequisites:

- Python virtual environment at `.venv`
- Node.js and npm
- Microsoft Visual C++ Build Tools with CMake support
- The first build can take a while because `llama-cpp-python` may compile a native wheel

To create a versioned Windows release artifact:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\release_exe.ps1
```

## Changing the Translation Model 🧠🔄

The app uses any GGUF-format model for translation and chat. To swap in a different model:

### Desktop (EXE)

1. Download the new GGUF model (e.g. from [Hugging Face](https://huggingface.co/models?library=gguf)).
2. Click **Open Models Folder** on the upload page — this opens `%LOCALAPPDATA%\RSVPReader\models` in Explorer.
3. Copy the new `.gguf` file into that folder.
4. Remove or rename the old `.gguf` if you want to guarantee the new one is picked up (the app always loads the first file found alphabetically).
5. Restart `RSVPReader.exe`.

To pin a specific model file instead of relying on auto-discovery, set the environment variable before launching:

```powershell
$env:LLAMA_MODEL_PATH = "C:\path\to\your-model.gguf"
& dist\RSVPReader.exe
```

### Local dev / Docker

Set `LLAMA_MODEL_PATH` in your `.env` file or shell:

```dotenv
LLAMA_MODEL_PATH=C:\path\to\your-model.gguf
```

Optional tuning variables (also in `.env`):

| Variable | Default | Description |
|---|---|---|
| `LLAMA_N_CTX` | `4096` | Context window size |
| `LLAMA_THREADS` | `4` | CPU threads for inference |
| `LLAMA_GPU_LAYERS` | `0` | Layers to offload to GPU (`0` = CPU only) |
| `LLAMA_CHUNK_WORDS` | `300` | Max words per translation request |

Any model that works with `llama-cpp-python` and produces readable text output will work — the translation prompt is plain text so there is no model-specific fine-tuning required.



- Fast upload + instant parsing 🚀📄
- Smooth RSVP playback controls 🎛️▶️
- Keyboard shortcuts for flow ⌨️⚡
- Theme/language/pacing personalization 🎨🌍🧠

## Quick Start 🚀

### Local dev 🛠️

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev -- --host
```

### Docker 🐳

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Docs 📚

- [Setup Guide](docs/SETUP.md)
- [Docker Guide](docs/DOCKER.md)
- [Environment Variables](docs/ENVIRONMENT.md)
- [API Reference](docs/API.md)
- [Desktop Build & Release](docs/DESKTOP_BUILD.md)
- [Project Structure & Stack](docs/PROJECT_OVERVIEW.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## Testing Assets 🧪

Smoke-test sample PDFs and JSON payload snapshots are now organized in [testing/smoke](testing/smoke).



## License 🧾⚖️

Choose and add a license file (for example MIT) 🧾