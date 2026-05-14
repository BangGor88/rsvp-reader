# Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 20+
- npm
- Docker + Docker Compose (optional)
- Windows PowerShell (for .ps1 scripts)
- Microsoft Visual C++ Build Tools with CMake (required to compile `llama-cpp-python` for the desktop EXE)

## Local Development (Without Docker)

Run backend and frontend in separate terminals from the repository root.

### Backend setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend API: `http://localhost:8000`

To enable translation and chat in dev mode, set `LLAMA_MODEL_PATH` before starting:

```powershell
$env:LLAMA_MODEL_PATH = "C:\path\to\your-model.gguf"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend setup

```powershell
cd frontend
npm install
npm run dev -- --host
```

Frontend app: `http://localhost:5173`