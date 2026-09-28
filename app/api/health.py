"""Health check and system status endpoint."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.schemas.health import HealthCheckResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns service health status and checks live database connectivity.",
)
def health_check(db: Session = Depends(get_db)) -> HealthCheckResponse:
    """Verifies service readiness and database connectivity."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return HealthCheckResponse(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
    )
