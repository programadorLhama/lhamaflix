from fastapi import APIRouter, FastAPI

from app.main.routes import health, videos


def register_routes(app: FastAPI) -> None:
    api = APIRouter(prefix="/api")
    api.include_router(health.router)
    api.include_router(videos.router)
    app.include_router(api)
