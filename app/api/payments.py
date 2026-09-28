"""Payment and webhook processing endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.payment import PaymentRequest, PaymentResponse
from app.schemas.webhook import PaymentWebhookRequest, PaymentWebhookResponse
from app.services.payment_service import PaymentService
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process simulated payment",
    description="Simulates a payment transaction for an authenticated user's booking. Updates booking status to CONFIRMED on SUCCESS or FAILED on FAILED.",
)
def process_payment(
    request: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    """Processes a simulated payment transaction."""
    payment = PaymentService.process_payment(
        db=db,
        user_id=current_user.id,
        request=request,
    )
    return payment


@router.post(
    "/webhook",
    response_model=PaymentWebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Payment provider webhook",
    description="Idempotent webhook endpoint accepting status notifications from the simulated payment gateway. Handles duplicate deliveries without corrupting state or duplicating records.",
)
def payment_webhook(
    request: PaymentWebhookRequest,
    db: Session = Depends(get_db),
) -> PaymentWebhookResponse:
    """Processes payment status webhooks idempotently."""
    return WebhookService.process_payment_webhook(db=db, request=request)


# Also support trailing slash if client calls /payments/webhook/
@router.post(
    "/webhook/",
    response_model=PaymentWebhookResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def payment_webhook_trailing_slash(
    request: PaymentWebhookRequest,
    db: Session = Depends(get_db),
) -> PaymentWebhookResponse:
    """Processes payment status webhooks idempotently (trailing slash handler)."""
    return WebhookService.process_payment_webhook(db=db, request=request)
