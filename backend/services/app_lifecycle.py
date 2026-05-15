import threading
from typing import Callable

_lock = threading.Lock()
_exit_handler: Callable[[], None] | None = None


def register_exit_handler(handler: Callable[[], None]) -> None:
    """Register a process-exit handler (used by the standalone EXE runtime)."""
    global _exit_handler
    with _lock:
        _exit_handler = handler


def can_exit_app() -> bool:
    with _lock:
        return _exit_handler is not None


def request_app_exit() -> bool:
    """Trigger the registered exit handler in a background thread."""
    with _lock:
        handler = _exit_handler

    if handler is None:
        return False

    def _run() -> None:
        try:
            handler()
        except Exception as exc:
            print(f"[ERROR] App exit handler failed: {exc}")

    threading.Thread(target=_run, daemon=True, name="app-exit").start()
    return True