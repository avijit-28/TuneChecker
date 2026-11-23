from fastapi import APIRouter
from app.api.v1 import health, calls, settings, dashboard

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(calls.router)
api_router.include_router(settings.router)
api_router.include_router(dashboard.router)
