"""Payment gateway webhook ingestion with strict idempotency and state safety."""

import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.core.exceptions import NotFoundException
from app.core.logging import logger
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.webhook_event import WebhookEvent
from app.schemas.webhook import PaymentWebhookRequest, PaymentWebhookResponse


class WebhookService:
    """Service handling payment provider webhooks with strict idempotency and state transition guards."""

    @staticmethod
    def process_payment_webhook(db: Session, request: PaymentWebhookRequest) -> PaymentWebhookResponse:
        """
        Processes incoming payment webhook events idempotently.
        - Deduplicates identical event_ids.
        - Guarantees transactional atomicity.
        - Protects finalized booking states against out-of-order or stale events.
        """
        # Step 1: Check if event_id has already been processed
        stmt_event = select(WebhookEvent).where(WebhookEvent.event_id == request.event_id)
        existing_event = db.execute(stmt_event).scalar_one_or_none()

        if existing_event and existing_event.processed:
            # Query current booking state for idempotent response
            booking = db.get(Booking, request.booking_id)
            booking_status = booking.status.value if booking else "UNKNOWN"
            logger.info(
                "Duplicate webhook event detected and ignored: event_id=%s, booking_id=%d",
                request.event_id,
                request.booking_id,
            )
            return PaymentWebhookResponse(
                status="duplicate",
                message="Webhook event has already been processed.",
                event_id=request.event_id,
                booking_id=request.booking_id,
                booking_status=booking_status,
            )

        # Step 2: Validate that target booking exists with row-level locking
        stmt_booking = select(Booking).where(Booking.id == request.booking_id).with_for_update()
        booking = db.execute(stmt_booking).scalar_one_or_none()
        if not booking:
            logger.warning(
                "Webhook received for non-existent booking: booking_id=%d, event_id=%s",
                request.booking_id,
                request.event_id,
            )
            raise NotFoundException(detail=f"Booking with ID {request.booking_id} referenced in webhook not found.")

        # Step 3: Record or retrieve webhook event in database
        if not existing_event:
            event_payload = json.dumps({
                "event_id": request.event_id,
                "event_type": request.event_type,
                "payment_id": request.payment_id,
                "booking_id": request.booking_id,
                "status": request.status.value,
                "amount": str(request.amount) if request.amount else str(booking.amount),
            })
            webhook_event = WebhookEvent(
                event_id=request.event_id,
                event_type=request.event_type,
                payload=event_payload,
                processed=False,
            )
            db.add(webhook_event)
            try:
                db.flush()
            except IntegrityError:
                # Concurrent race condition caught by UNIQUE constraint on event_id
                db.rollback()
                logger.info(
                    "Concurrent webhook duplicate caught via UNIQUE constraint: event_id=%s",
                    request.event_id,
                )
                refetched_booking = db.get(Booking, request.booking_id)
                return PaymentWebhookResponse(
                    status="duplicate",
                    message="Webhook event has already been processed.",
                    event_id=request.event_id,
                    booking_id=request.booking_id,
                    booking_status=refetched_booking.status.value if refetched_booking else "UNKNOWN",
                )
        else:
            webhook_event = existing_event

        # Step 4: Record or update payment record linked to provider_payment_id
        stmt_pay = select(Payment).where(Payment.provider_payment_id == request.payment_id)
        payment_record = db.execute(stmt_pay).scalar_one_or_none()

        payment_amount = request.amount if request.amount is not None else booking.amount

        if not payment_record:
            payment_record = Payment(
                booking_id=booking.id,
                provider_payment_id=request.payment_id,
                amount=payment_amount,
                status=request.status,
            )
            db.add(payment_record)
        else:
            payment_record.status = request.status

        # Step 5: Apply protected state transition rules
        current_booking_status = booking.status

        if request.status == PaymentStatus.SUCCESS:
            if current_booking_status in (BookingStatus.PENDING, BookingStatus.FAILED):
                booking.status = BookingStatus.CONFIRMED
                logger.info(
                    "Booking %d transitioned from %s to CONFIRMED via webhook %s",
                    booking.id,
                    current_booking_status.value,
                    request.event_id,
                )
            elif current_booking_status == BookingStatus.CANCELLED:
                logger.warning(
                    "Payment SUCCESS webhook received for CANCELLED booking %d. State remains CANCELLED.",
                    booking.id,
                )
            elif current_booking_status == BookingStatus.CONFIRMED:
                logger.info(
                    "Payment SUCCESS webhook received for already CONFIRMED booking %d. State unchanged.",
                    booking.id,
                )

        elif request.status == PaymentStatus.FAILED:
            if current_booking_status == BookingStatus.PENDING:
                booking.status = BookingStatus.FAILED
                logger.info(
                    "Booking %d transitioned from PENDING to FAILED via webhook %s",
                    booking.id,
                    request.event_id,
                )
            elif current_booking_status == BookingStatus.CONFIRMED:
                # CRITICAL: Protect already-finalized confirmed booking from being downgraded by stale failure events
                logger.warning(
                    "Out-of-order FAILED webhook %s received for already CONFIRMED booking %d. Preserving CONFIRMED status.",
                    request.event_id,
                    booking.id,
                )
            elif current_booking_status in (BookingStatus.CANCELLED, BookingStatus.FAILED):
                logger.info(
                    "Payment FAILED webhook received for booking %d in state %s. State unchanged.",
                    booking.id,
                    current_booking_status.value,
                )

        # Step 6: Mark webhook event as processed and commit atomically
        webhook_event.processed = True
        webhook_event.processed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(booking)

        logger.info(
            "Webhook event %s processed successfully for Booking %d -> Status: %s",
            request.event_id,
            booking.id,
            booking.status.value,
        )

        return PaymentWebhookResponse(
            status="success",
            message="Webhook event processed successfully.",
            event_id=request.event_id,
            booking_id=booking.id,
            booking_status=booking.status.value,
        )
