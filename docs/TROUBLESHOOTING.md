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

### Desktop AI stays offline on another PC (`WinError 0xc000001d`)

If the log shows `Windows Error 0xc000001d`, this is typically a binary compatibility issue (illegal CPU/GPU instruction), not a missing Python dependency.

Common causes:
- A CUDA-enabled build was distributed to a machine with incompatible GPU driver/runtime.
- CPU instruction mismatch on the target machine.

What to do:
1. Rebuild and distribute a CPU-only EXE (default behavior of `scripts\build_exe.ps1`).
	 - If it still fails on that PC, build a legacy binary on the build machine:
		 - PowerShell: `$env:RSVP_LLAMA_LEGACY = "1"; .\\scripts\\build_exe.ps1`
     - This recompiles the current `llama-cpp-python` from source with conservative CPU flags (no AVX/AVX2/FMA/F16C, no OpenMP/BLAS, no GPU backends, SSE2 compiler target).
     - To try an older runtime explicitly, override legacy version:
			 - PowerShell: `$env:RSVP_LLAMA_LEGACY = "1"; $env:RSVP_LLAMA_LEGACY_VERSION = "0.2.90"; .\\scripts\\build_exe.ps1`
2. On the target PC, install **Microsoft Visual C++ Redistributable 2015-2022 (x64)**.
3. Ensure the model exists at `%LOCALAPPDATA%\RSVPReader\models\`.
4. If needed, force CPU mode with `LLAMA_GPU_LAYERS=0` in the environment before launch.

If you intentionally want a CUDA build, set `RSVP_ENABLE_CUDA_BUILD=1` before running the build script and verify target GPU/driver compatibility.

### Desktop EXE crashes immediately with no window

This was caused by uvicorn's logging formatter calling `sys.stdout.isatty()` when `sys.stdout` is `None` in a windowed (no-console) PyInstaller build. Fixed in `desktop_main.py` by redirecting stdio to the log file before any imports. If you see this with an old build, rebuild the EXE.