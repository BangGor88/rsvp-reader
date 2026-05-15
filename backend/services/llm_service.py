import os
import subprocess
import threading
from pathlib import Path

_lock = threading.Lock()
_model = None
_loading = False  # True while a model load is in progress


def is_model_loaded() -> bool:
    return _model is not None


def is_model_loading() -> bool:
    return _loading


def unload_model() -> None:
    """Unload the model from memory, freeing GPU/RAM."""
    global _model
    with _lock:
        if _model is not None:
            del _model
            _model = None
        print("[INFO] AI model unloaded.")


def _load_silently() -> None:
    """Background wrapper for get_model() that swallows exceptions to stderr/log."""
    try:
        get_model()
    except Exception as exc:
        print(f"[ERROR] Background model load failed: {exc}")


def load_model_async() -> None:
    """Trigger a model load in the background without blocking the caller."""
    if _model is not None or _loading:
        return
    threading.Thread(target=_load_silently, daemon=True, name="llm-load").start()


def _default_threads() -> int:
    """Use all physical/logical cores up to 8; fall back to 4 if detection fails."""
    try:
        count = os.cpu_count() or 4
        return min(count, 8)
    except Exception:
        return 4


def _detect_gpu_layers() -> int:
    """Return n_gpu_layers default.

    Returns -1 (offload all layers) when an Nvidia GPU is detected via
    nvidia-smi, so the CUDA-enabled llama-cpp-python wheel can make use of it.
    Falls back to 0 (CPU-only) when no GPU is found or detection fails.
    Override at any time by setting LLAMA_GPU_LAYERS in the environment.
    """
    explicit = os.getenv("LLAMA_GPU_LAYERS", "").strip()
    if explicit:
        return int(explicit)

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            gpu_name = result.stdout.strip().splitlines()[0]
            print(f"[INFO] GPU detected: {gpu_name} — enabling full GPU offload (n_gpu_layers=-1)")
            return -1
    except Exception:
        pass

    return 0


def get_model():
    global _model, _loading
    if _model is not None:
        return _model

    with _lock:
        if _model is not None:
            return _model

        model_path = os.getenv("LLAMA_MODEL_PATH", "")
        if not model_path:
            raise RuntimeError(
                "LLAMA_MODEL_PATH is not set. "
                "Add it to .env or place a GGUF model in the app models directory, "
                "e.g. %LOCALAPPDATA%\\RSVPReader\\models\\your-model.gguf"
            )
        if not Path(model_path).exists():
            raise RuntimeError(f"Model file not found: {model_path}")

        from llama_cpp import Llama

        _loading = True
        try:
            _model = Llama(
                model_path=model_path,
                n_ctx=int(os.getenv("LLAMA_N_CTX", "2048")),
                n_threads=int(os.getenv("LLAMA_THREADS", str(_default_threads()))),
                n_batch=int(os.getenv("LLAMA_N_BATCH", "512")),
                n_gpu_layers=_detect_gpu_layers(),
                verbose=False,
            )
        finally:
            _loading = False
        return _model
