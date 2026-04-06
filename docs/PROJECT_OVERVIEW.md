# Project Overview

## What This Project Includes

- FastAPI backend for PDF upload, parsing, and word/page retrieval.
- React + Vite frontend for upload flow and RSVP reading experience.
- Docker setup for development and production-style local deployment.
- Windows executable packaging via PyInstaller.

## Features

- PDF upload and text extraction.
- Per-document metadata: word count, page count, page word ranges.
- Start reading from a selected page or exact word index.
- Playback controls: play/pause, seek, WPM up/down.
- Keyboard shortcuts:
  - Space: play/pause
  - Left/Right: back/forward 10 words
  - Up/Down: WPM +/- 20
  - Escape: close settings panel
  - ?: toggle shortcuts help
- Reader personalization:
  - WPM (20-400)
  - Font size
  - Focus-letter index
  - Reader stage position
  - ORP color
  - Theme (light/dark)
  - Language selection

## Tech Stack

- Backend: FastAPI, Uvicorn, PyMuPDF, python-dotenv
- Frontend: React 18, Vite, Axios
- Containers: Docker, Docker Compose, Nginx
- Packaging: PyInstaller (Windows)

## Project Structure

```text
rsvp-reader/
  backend/
    main.py                # API app + static SPA serving
    desktop_main.py        # Desktop launcher entrypoint
    routers/pdf.py         # PDF endpoints
    services/pdf_service.py# PDF parsing logic
    static/                # Built frontend assets copied for backend/desktop
  frontend/
    src/
      screens/             # Upload and reader screens
      hooks/               # useRSVP, useSettings
      components/          # Reader UI controls and display
  scripts/
    build_exe.ps1          # Build frontend + create RSVPReader.exe
    release_exe.ps1        # Create release folder + checksum + notes
  docker-compose.yml       # Production-style local stack (frontend via Nginx)
  docker-compose.dev.yml   # Live-reload development stack
  RSVPReader.spec          # PyInstaller spec
```