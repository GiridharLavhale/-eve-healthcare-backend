"""Payment provider webhook request and response schemas."""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from app.models.payment import PaymentStatus


class PaymentWebhookRequest(BaseModel):
    """Incoming payment provider webhook event payload."""
    event_id: str = Field(..., min_length=1, max_length=100, description="Unique event identifier from payment gateway")
    event_type: str = Field(default="payment.updated", description="Type of event")
    payment_id: str = Field(..., min_length=1, max_length=100, description="Payment provider transaction reference")
    booking_id: int = Field(..., gt=0, description="Internal booking ID")
    status: PaymentStatus = Field(..., description="Payment outcome status (SUCCESS or FAILED)")
    amount: Optional[Decimal] = Field(None, gt=0, description="Amount paid, optional verification")


class PaymentWebhookResponse(BaseModel):
    """Webhook processing response."""
    status: str = Field(..., description="Processing status: 'success', 'duplicate', or 'ignored'")
    message: str = Field(..., description="Human-readable result summary")
    event_id: str = Field(..., description="Processed event ID")
    booking_id: int = Field(..., description="Associated booking ID")
    booking_status: str = Field(..., description="Current booking status following event processing")
