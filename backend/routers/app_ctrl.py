from fastapi import APIRouter, HTTPException

from services.app_lifecycle import can_exit_app, request_app_exit

router = APIRouter(prefix="/app", tags=["app"])


@router.get("/status")
def app_status() -> dict[str, bool]:
    return {"canExit": can_exit_app()}


@router.post("/exit")
def exit_app() -> dict[str, str]:
    if not request_app_exit():
        raise HTTPException(status_code=503, detail="App exit is not available in this runtime")
    return {"status": "exiting"}