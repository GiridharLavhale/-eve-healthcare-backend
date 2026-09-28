"""EVE Healthcare Backend Application entrypoint."""

import time
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
# EVE Healthcare Diagnostic Test Booking & Simulated Payment Backend

A high-reliability, production-grade backend service for managing diagnostic centres, 
test catalogues, patient bookings, and idempotent payment webhooks.

### Core Features:
- **Authentication**: JWT-based secure authentication with bcrypt password hashing.
- **Diagnostic Centres & Tests**: Complete cataloguing and location-specific pricing.
- **Booking Engine**: Future-date validation, price snapshotting, and atomic status transitions.
- **Simulated Payment Gateway**: Deterministic payment simulation and booking confirmation.
- **Idempotent Webhooks**: Strict deduplication, race condition protection, and state safety guards.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Logs incoming requests, duration, and status codes safely."""
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "%s %s -> status=%d (took %.2fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# Global Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handles domain-level application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Transforms Pydantic validation errors into clear client error messages."""
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append({
            "field": field,
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type", "validation_error"),
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "detail": "Request validation failed.",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled exceptions safely without exposing internal stack traces."""
    logger.exception("Unhandled server error processing %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# Mount API Router
app.include_router(api_router, prefix=settings.API_V1_STR)
