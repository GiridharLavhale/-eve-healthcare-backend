"""Payment schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.payment import PaymentStatus


class PaymentRequest(BaseModel):
    """Payment initiation request schema."""
    booking_id: int = Field(..., gt=0, description="ID of booking to pay for")
    simulate_result: Optional[PaymentStatus] = Field(
        default=PaymentStatus.SUCCESS,
        description="Simulated payment outcome for testing (SUCCESS or FAILED)",
    )


class PaymentResponse(BaseModel):
    """Payment transaction details response."""
    id: int
    booking_id: int
    provider_payment_id: Optional[str]
    amount: Decimal
    status: PaymentStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
