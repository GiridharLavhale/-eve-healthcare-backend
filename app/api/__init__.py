"""API Routers aggregation."""

from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.centres import router as centres_router
from app.api.tests import router as tests_router
from app.api.bookings import router as bookings_router
from app.api.payments import router as payments_router
from app.api.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(centres_router)
api_router.include_router(tests_router)
api_router.include_router(bookings_router)
api_router.include_router(payments_router)

__all__ = ["api_router"]
