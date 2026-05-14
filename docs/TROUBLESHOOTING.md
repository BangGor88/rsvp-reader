# Troubleshooting

## Notes and Limitations

- Text extraction quality depends on PDF content and encoding.
- Image-only PDFs are detected heuristically (`image_only` flag), and extraction may be incomplete.
- In-memory document cache is process-local; restarting backend clears cache.

## Common Issues

### 422 Only PDF files are supported

Ensure uploaded file has a `.pdf` extension.

### Unable to parse PDF

File may be corrupted, encrypted, or not text-extractable.

### Frontend cannot reach backend

- Confirm backend is running on port `8000`.
- Confirm CORS via `ALLOWED_ORIGINS` when using non-default frontend ports.

### Desktop app fails to launch UI

Ensure `backend/static/index.html` exists in packaged assets (handled by build script).

### Desktop app shows "Translation failed"

1. Check the runtime log at `%LOCALAPPDATA%\RSVPReader\rsvpreader.log` for the full error.
2. Confirm a `.gguf` model file is present in `%LOCALAPPDATA%\RSVPReader\models\`. Use the **Open Models Folder** button on the upload page.
3. If the log shows a `FileNotFoundError` for `llama_cpp/lib`, rebuild the EXE — the `RSVPReader.spec` now bundles the required DLLs. Run `scripts\build_exe.ps1` again.

### Desktop app shows no startup dialog but translation never works

The model may have failed to load silently. Check `rsvpreader.log`. Common causes:
- Model file is corrupt or an unsupported GGUF version.
- Insufficient RAM for the model's context size (reduce `LLAMA_N_CTX`).
- `LLAMA_MODEL_PATH` environment variable points to a file that no longer exists.

### Desktop EXE crashes immediately with no window

This was caused by uvicorn's logging formatter calling `sys.stdout.isatty()` when `sys.stdout` is `None` in a windowed (no-console) PyInstaller build. Fixed in `desktop_main.py` by redirecting stdio to the log file before any imports. If you see this with an old build, rebuild the EXE.