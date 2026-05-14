# Environment Variables

Backend reads environment variables from `.env` (when provided).

## Variables

- `ALLOWED_ORIGINS`: comma-separated CORS origins.
  - Default: `http://localhost:3000`
- `UPLOAD_DIR`: directory for uploaded PDFs.
  - Default: `<repo>/uploads` (or `/app/uploads` in containers)
- `EBOOK_LIBRARY_DIR`: directory used as the ebook library (uploaded files are stored here).
  - Default: `<UPLOAD_DIR>/ebooks`
- `MODELS_DIR`: directory scanned for GGUF model files.
  - Desktop standalone default: `%LOCALAPPDATA%\RSVPReader\models`
  - Container default: `<repo>/backend/models`
- `LLAMA_MODEL_PATH`: explicit path to the GGUF model used by llama.cpp.
  - Desktop standalone default behavior: auto-discovered from `MODELS_DIR` and several fallback directories; no explicit setting needed if the model is in `%LOCALAPPDATA%\RSVPReader\models`
- `LLAMA_N_CTX`: llama.cpp context window size. Default: `4096`.
- `LLAMA_THREADS`: CPU thread count for inference. Default: `4`.
- `LLAMA_GPU_LAYERS`: number of layers to offload to GPU. Default: `0` (CPU-only).
- `LLAMA_CHUNK_WORDS`: max words per translation chunk. Default: `300`.
- `FRONTEND_DIST`: path to built frontend files to serve from backend.
  - Default fallback: `backend/static`, then `frontend/dist`
- `RSVP_BUILD_VERSION`: explicit build version string shown in the app and `/api/health`.
  - If unset, the app falls back to embedded `build_version.txt`, then latest `release\RELEASE_NOTES.txt`, then `dev`