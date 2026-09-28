"""Simulated payment processing business logic and state transitions."""

import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.core.logging import logger
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentRequest


class PaymentService:
    """Service handling simulated payment processing and booking status updates."""

    @staticmethod
    def process_payment(db: Session, user_id: int, request: PaymentRequest) -> Payment:
        """
        Simulates payment for a user's booking.
        - Validates booking existence and ownership.
        - Locks the booking row (with_for_update) to prevent concurrent race conditions.
        - Validates booking is in PENDING state.
        - Creates payment record and transitions booking status atomically.
        """
        stmt_booking = select(Booking).where(Booking.id == request.booking_id).with_for_update()
        booking = db.execute(stmt_booking).scalar_one_or_none()
        if not booking:
            raise NotFoundException(detail=f"Booking with ID {request.booking_id} not found.")

        if booking.user_id != user_id:
            raise ForbiddenException(detail="You are not authorized to process payment for this booking.")

        # State checks
        if booking.status == BookingStatus.CONFIRMED:
            raise BadRequestException(detail="Booking is already paid and confirmed.")

        if booking.status == BookingStatus.CANCELLED:
            raise BadRequestException(detail="Cannot process payment for a cancelled booking.")

        if booking.status == BookingStatus.FAILED:
            raise BadRequestException(detail="Cannot process payment for a failed booking.")

        if booking.status != BookingStatus.PENDING:
            raise BadRequestException(
                detail=f"Cannot process payment for booking in state '{booking.status.value}'."
            )

        # Determine outcome
        outcome = request.simulate_result or PaymentStatus.SUCCESS
        provider_id = f"sim_pay_{uuid.uuid4().hex[:16]}"

        payment = Payment(
            booking_id=booking.id,
            provider_payment_id=provider_id,
            amount=booking.amount,
            status=outcome,
        )
        db.add(payment)

        # Transition booking status
        if outcome == PaymentStatus.SUCCESS:
            booking.status = BookingStatus.CONFIRMED
        else:
            booking.status = BookingStatus.FAILED

        db.commit()
        db.refresh(payment)
        db.refresh(booking)

        logger.info(
            "Simulated payment processed: PaymentID=%d, BookingID=%d, Status=%s, ProviderRef=%s",
            payment.id,
            booking.id,
            outcome.value,
            provider_id,
        )
        return payment
