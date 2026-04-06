# RSVP Reader Master Prompt

## Goal
Build and maintain a local-first RSVP reader application with these priorities:
- Fast PDF upload and word extraction.
- Smooth RSVP playback controls and accessibility shortcuts.
- Clean Docker workflow for frontend and backend services.
- Optional Windows executable packaging for one-file distribution.

## Current Architecture
- Frontend: React + Vite
- Backend: FastAPI + PyMuPDF
- Containers: frontend + backend only
- Packaging: PyInstaller single-file executable

## Runtime Endpoints
- Web app: `/`
- Health: `/api/health`
- Upload PDF: `POST /api/pdf/upload`
- Fetch words: `GET /api/pdf/words/{doc_id}`
- Delete document: `DELETE /api/pdf/{doc_id}`

## Docker Notes
- Start: `docker compose up --build -d`
- Stop: `docker compose down`
- Health smoke check: `http://127.0.0.1:8010/api/health`

## Executable Notes
- Build: `powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1`
- Release: `powershell -ExecutionPolicy Bypass -File scripts/release_exe.ps1`
- Output binary: `dist/RSVPReader.exe`

## Quality Gates
- Upload a sample PDF and verify `word_count > 0`.
- Verify `/api/health` returns backend status.
- Verify keyboard controls and WPM step behavior in the reader.
- Verify executable startup error is clear when the port is already in use.