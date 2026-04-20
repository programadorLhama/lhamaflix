from fastapi import APIRouter

from app.controllers.health import health_status

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return health_status()
