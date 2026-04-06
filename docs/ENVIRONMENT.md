# Environment Variables

Backend reads environment variables from `.env` (when provided).

## Variables

- `ALLOWED_ORIGINS`: comma-separated CORS origins.
  - Default: `http://localhost:3000`
- `UPLOAD_DIR`: directory for uploaded PDFs.
  - Default: `<repo>/uploads` (or `/app/uploads` in containers)
- `FRONTEND_DIST`: path to built frontend files to serve from backend.
  - Default fallback: `backend/static`, then `frontend/dist`