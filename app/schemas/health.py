"""Health check schema."""

from datetime import datetime
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    status: str = Field(default="ok", description="Overall service status")
    database: str = Field(..., description="Database connection status ('connected' or 'disconnected')")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Current server UTC timestamp")
