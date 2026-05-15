import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from build_info import get_build_version
from routers.ai_ctrl import router as ai_ctrl_router
from routers.app_ctrl import router as app_ctrl_router
from routers.pdf import router as pdf_router
from routers.translate import router as translate_router

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_FRONTEND_DIST = BASE_DIR / "static"


def _allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _resolve_frontend_dist() -> Path:
    configured = Path(os.getenv("FRONTEND_DIST", str(DEFAULT_FRONTEND_DIST)))
    if configured.exists():
        return configured

    local_dist = BASE_DIR.parent / "frontend" / "dist"
    if local_dist.exists():
        return local_dist

    return configured


def _mount_frontend(app: FastAPI, frontend_dist: Path) -> None:
    if not frontend_dist.exists():
        return

    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.middleware("http")
    async def spa_fallback(request: Request, call_next: Any) -> Any:
        response = await call_next(request)
        if response.status_code == 404 and not request.url.path.startswith("/api"):
            index = frontend_dist / "index.html"
            if index.exists():
                return FileResponse(index)
        return response


def create_app() -> FastAPI:
    app = FastAPI(title="RSVP Reader API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(pdf_router, prefix="/api")
    app.include_router(translate_router, prefix="/api")
    app.include_router(ai_ctrl_router, prefix="/api")
    app.include_router(app_ctrl_router, prefix="/api")

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {"backend": "ok", "build": get_build_version()}

    _mount_frontend(app, _resolve_frontend_dist())
    return app


app = create_app()
