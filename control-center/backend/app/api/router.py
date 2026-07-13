"""Router principal de la API."""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.system import router as system_router
from app.core.constants import API_PREFIX

api_router = APIRouter(prefix=API_PREFIX)

api_router.include_router(health_router)
api_router.include_router(system_router)
