from fastapi import APIRouter

from services.llm_service import (
    is_model_loaded,
    is_model_loading,
    load_model_async,
    unload_model,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
def ai_status():
    if is_model_loading():
        return {"status": "loading"}
    return {"status": "online" if is_model_loaded() else "offline"}


@router.post("/stop")
def stop_ai():
    unload_model()
    return {"status": "offline"}


@router.post("/start")
def start_ai():
    if not is_model_loaded() and not is_model_loading():
        load_model_async()
    return {"status": "loading" if not is_model_loaded() else "online"}
