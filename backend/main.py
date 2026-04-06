import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from routers.pdf import router as pdf_router

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

    @app.get("/", include_in_schema=False)
    def serve_frontend_root() -> FileResponse:
        return FileResponse(frontend_dist / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend_spa(full_path: str) -> FileResponse:
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found")

        requested = frontend_dist / full_path
        if requested.is_file():
            return FileResponse(requested)

        return FileResponse(frontend_dist / "index.html")


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
    _mount_frontend(app, _resolve_frontend_dist())
    return app


app = create_app()


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "backend": "ok",
    }
