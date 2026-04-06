import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn
from main import app


HOST = "127.0.0.1"
PORT = 8000


def _configure_runtime_paths() -> tuple[Path, Path]:
    base_dir = Path(__file__).resolve().parent

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundle_dir = Path(str(getattr(sys, "_MEIPASS", "")))
        frontend_dist = bundle_dir / "static"
    else:
        frontend_dist = base_dir / "static"
        if not frontend_dist.exists():
            frontend_dist = base_dir.parent / "frontend" / "dist"

    upload_dir = Path.cwd() / "uploads"
    os.environ.setdefault("FRONTEND_DIST", str(frontend_dist))
    os.environ.setdefault("UPLOAD_DIR", str(upload_dir))
    return frontend_dist, upload_dir


def _validate_paths(frontend_dist: Path, upload_dir: Path) -> None:
    index_file = frontend_dist / "index.html"
    if not index_file.exists():
        print(f"[ERROR] Frontend assets not found at: {frontend_dist}")
        print("[ERROR] Expected index file is missing: index.html")
        raise SystemExit(1)

    upload_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Frontend directory: {frontend_dist}")
    print(f"[INFO] Upload directory: {upload_dir}")


def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def _guard_port(host: str, port: int) -> None:
    if _port_in_use(host, port):
        print(f"[ERROR] Port {port} is already in use on {host}.")
        print("[ERROR] Close the app using that port and try again.")
        raise SystemExit(1)


def _open_browser() -> None:
    time.sleep(1.2)
    webbrowser.open(f"http://{HOST}:{PORT}")


def main() -> None:
    frontend_dist, upload_dir = _configure_runtime_paths()
    _validate_paths(frontend_dist, upload_dir)
    _guard_port(HOST, PORT)
    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
