# ── stdio must be redirected BEFORE any other import ─────────────────────────
# PyInstaller windowed (console=False) EXEs have sys.stdout/stderr == None.
# uvicorn's DefaultFormatter calls sys.stdout.isatty() at import time, which
# crashes if the stream is None. Redirect to a log file immediately.
import sys
import os as _os

if getattr(sys, "frozen", False) and sys.stderr is None:
    _local = _os.getenv("LOCALAPPDATA") or _os.path.join(
        _os.path.expanduser("~"), "AppData", "Local"
    )
    _log_dir = _os.path.join(_local, "RSVPReader")
    _os.makedirs(_log_dir, exist_ok=True)
    _logfile = open(
        _os.path.join(_log_dir, "rsvpreader.log"), "w", encoding="utf-8", buffering=1
    )
    sys.stdout = _logfile
    sys.stderr = _logfile
# ─────────────────────────────────────────────────────────────────────────────

import os
import socket
import threading
import time
import webbrowser
import ctypes
from pathlib import Path

import uvicorn
from main import app


HOST = "127.0.0.1"
PORT = 8000


def _show_error_dialog(title: str, message: str) -> None:
    if not sys.platform.startswith("win"):
        return
    try:
        ctypes.windll.user32.MessageBoxW(None, message, title, 0x00000010)
    except Exception:
        pass


def _fatal_error(title: str, message: str) -> None:
    print(f"[ERROR] {message}")
    _show_error_dialog(title, message)
    raise SystemExit(1)


def _app_data_root() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA", "").strip()
    if local_app_data:
        return Path(local_app_data) / "RSVPReader"

    user_profile = os.getenv("USERPROFILE", "").strip()
    if user_profile:
        return Path(user_profile) / "AppData" / "Local" / "RSVPReader"

    return Path.cwd() / ".rsvp-reader"


def _resolve_model_path(models_dir: Path) -> str:
    configured = os.getenv("LLAMA_MODEL_PATH", "").strip()
    if configured and Path(configured).exists():
        return configured

    search_dirs = [models_dir]

    exe_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path.cwd()
    search_dirs.append(exe_dir / "models")
    search_dirs.append(Path.cwd() / "models")
    search_dirs.append(Path.cwd() / "backend" / "models")

    seen: set[str] = set()
    for directory in search_dirs:
        key = str(directory.resolve()) if directory.exists() else str(directory)
        if key in seen:
            continue
        seen.add(key)

        gguf_files = sorted(directory.glob("*.gguf")) if directory.exists() else []
        if gguf_files:
            return str(gguf_files[0])

    return ""


def _configure_runtime_paths() -> tuple[Path, Path, Path, Path]:
    base_dir = Path(__file__).resolve().parent

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundle_dir = Path(str(getattr(sys, "_MEIPASS", "")))
        frontend_dist = bundle_dir / "static"
    else:
        frontend_dist = base_dir / "static"
        if not frontend_dist.exists():
            frontend_dist = base_dir.parent / "frontend" / "dist"

    app_data_dir = _app_data_root()
    upload_dir = app_data_dir / "uploads"
    ebook_library_dir = upload_dir / "ebooks"
    models_dir = app_data_dir / "models"

    os.environ.setdefault("FRONTEND_DIST", str(frontend_dist))
    os.environ.setdefault("UPLOAD_DIR", str(upload_dir))
    os.environ.setdefault("EBOOK_LIBRARY_DIR", str(ebook_library_dir))
    os.environ.setdefault("MODELS_DIR", str(models_dir))

    resolved_model_path = _resolve_model_path(models_dir)
    if resolved_model_path:
        os.environ.setdefault("LLAMA_MODEL_PATH", resolved_model_path)

    return frontend_dist, upload_dir, ebook_library_dir, models_dir


def _validate_paths(frontend_dist: Path, upload_dir: Path, ebook_library_dir: Path, models_dir: Path) -> None:
    index_file = frontend_dist / "index.html"
    if not index_file.exists():
        _fatal_error(
            "RSVPReader Startup Error",
            f"Frontend assets not found at: {frontend_dist}"
        )

    upload_dir.mkdir(parents=True, exist_ok=True)
    ebook_library_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Frontend directory: {frontend_dist}")
    print(f"[INFO] Upload directory: {upload_dir}")
    print(f"[INFO] Ebook library directory: {ebook_library_dir}")
    print(f"[INFO] Models directory: {models_dir}")


def _validate_model_path(models_dir: Path) -> None:
    model_path = os.getenv("LLAMA_MODEL_PATH", "").strip()
    if not model_path:
        fallback = _resolve_model_path(models_dir)
        if fallback:
            os.environ["LLAMA_MODEL_PATH"] = fallback
            print(f"[INFO] Fallback model selected: {fallback}")
            return

        _fatal_error(
            "RSVPReader Model Required",
            "No GGUF model found. Place a .gguf file in:\n"
            f"{models_dir}\n\n"
            "Then restart RSVPReader."
        )

    resolved = Path(model_path)
    if not resolved.exists():
        gguf_files = sorted(models_dir.glob("*.gguf"))
        if gguf_files:
            os.environ["LLAMA_MODEL_PATH"] = str(gguf_files[0])
            print(f"[INFO] Fallback model selected: {gguf_files[0]}")
            return

        _fatal_error(
            "RSVPReader Model Missing",
            "Configured model file was not found:\n"
            f"{resolved}\n\n"
            "Update LLAMA_MODEL_PATH or place the model in the app models folder."
        )


def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def _guard_port(host: str, port: int) -> None:
    if _port_in_use(host, port):
        _fatal_error(
            "RSVPReader Port In Use",
            f"Port {port} is already in use on {host}.\n"
            "Close the app or process using that port and try again."
        )


def _open_browser() -> None:
    time.sleep(1.2)
    webbrowser.open(f"http://{HOST}:{PORT}")


def main() -> None:
    frontend_dist, upload_dir, ebook_library_dir, models_dir = _configure_runtime_paths()
    _validate_paths(frontend_dist, upload_dir, ebook_library_dir, models_dir)
    _validate_model_path(models_dir)
    _guard_port(HOST, PORT)
    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
        log_config=None,
        access_log=False,
    )


if __name__ == "__main__":
    main()
