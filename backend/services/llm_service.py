import os
import threading
from pathlib import Path

_lock = threading.Lock()
_model = None


def get_model():
    global _model
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

        _model = Llama(
            model_path=model_path,
            n_ctx=int(os.getenv("LLAMA_N_CTX", "4096")),
            n_threads=int(os.getenv("LLAMA_THREADS", "4")),
            n_gpu_layers=int(os.getenv("LLAMA_GPU_LAYERS", "0")),
            verbose=False,
        )
        return _model
