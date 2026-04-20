from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.configs.settings import settings
from app.main.routes import register_routes
from app.models.database import init_db


def _ensure_dirs() -> None:
    settings.videos_dir.mkdir(parents=True, exist_ok=True)
    settings.hls_dir.mkdir(parents=True, exist_ok=True)
    settings.static_dir.mkdir(parents=True, exist_ok=True)
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)


def create_app() -> FastAPI:
    application = FastAPI(title="HLS Streaming API", version="0.1.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.on_event("startup")
    def on_startup() -> None:
        _ensure_dirs()
        init_db()

    register_routes(application)
    application.mount("/hls", StaticFiles(directory=str(settings.hls_dir)), name="hls")
    application.mount(
        "/",
        StaticFiles(directory=str(settings.static_dir), html=True),
        name="static",
    )
    return application


app = create_app()
