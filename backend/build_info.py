import os
from pathlib import Path


def _build_version_file() -> Path:
    return Path(__file__).resolve().parent / "build_version.txt"


def _release_root() -> Path:
    return Path(__file__).resolve().parent.parent / "release"


def _latest_release_notes() -> Path | None:
    release_root = _release_root()
    if not release_root.exists():
        return None

    release_dirs = [path for path in release_root.iterdir() if path.is_dir()]
    if not release_dirs:
        return None

    latest_dir = max(release_dirs, key=lambda path: path.name)
    notes_path = latest_dir / "RELEASE_NOTES.txt"
    if notes_path.exists():
        return notes_path
    return None


def get_build_version() -> str:
    env_version = os.getenv("RSVP_BUILD_VERSION", "").strip()
    if env_version:
        return env_version

    version_file = _build_version_file()
    if version_file.exists():
        try:
            version = version_file.read_text(encoding="utf-8").strip()
            if version:
                return version
        except Exception:
            pass

    notes_path = _latest_release_notes()
    if notes_path is not None:
        try:
            for line in notes_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("Version:"):
                    version = line.split(":", 1)[1].strip()
                    if version:
                        return version
        except Exception:
            pass

    return "dev"
