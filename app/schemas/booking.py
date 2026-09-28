"""Booking request, response, and lifecycle schemas."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.booking import BookingStatus
from app.schemas.diagnostic_centre import DiagnosticCentreResponse
from app.schemas.diagnostic_test import DiagnosticTestResponse


class BookingCreate(BaseModel):
    """Booking creation request schema."""
    centre_id: int = Field(..., gt=0, description="ID of diagnostic centre")
    test_id: int = Field(..., gt=0, description="ID of diagnostic test")
    appointment_datetime: datetime = Field(
        ...,
        description="Scheduled appointment date and time (must be in the future)",
    )

    @field_validator("appointment_datetime")
    @classmethod
    def validate_future_appointment(cls, v: datetime) -> datetime:
        # Normalize timezone
        now = datetime.now(timezone.utc)
        if v.tzinfo is None:
            # Assume UTC if naive
            v_aware = v.replace(tzinfo=timezone.utc)
        else:
            v_aware = v.astimezone(timezone.utc)

        if v_aware <= now:
            raise ValueError("Appointment datetime must be in the future.")
        return v_aware


class BookingResponse(BaseModel):
    """Booking details response schema."""
    id: int
    user_id: int
    centre_id: int
    test_id: int
    appointment_datetime: datetime
    amount: Decimal
    status: BookingStatus
    created_at: datetime
    updated_at: datetime
    centre: Optional[DiagnosticCentreResponse] = None
    test: Optional[DiagnosticTestResponse] = None

    model_config = ConfigDict(from_attributes=True)


class BookingCancelResponse(BaseModel):
    """Booking cancellation response schema."""
    id: int
    status: BookingStatus
    message: str
