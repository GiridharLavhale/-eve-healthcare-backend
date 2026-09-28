"""Booking management business logic, ownership checks, and state transitions."""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.core.logging import logger
from app.models.booking import Booking, BookingStatus
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.diagnostic_test import DiagnosticTest
from app.models.centre_test import CentreTest
from app.schemas.booking import BookingCreate


class BookingService:
    """Service managing appointment booking lifecycle, price snapshotting, and cancellation."""

    @staticmethod
    def create_booking(db: Session, user_id: int, request: BookingCreate) -> Booking:
        """
        Creates a diagnostic test booking for an authenticated user.
        - Verifies centre and test existence.
        - Verifies centre offers the test and captures current price.
        - Initializes booking status to PENDING.
        """
        # Validate centre
        centre = db.get(DiagnosticCentre, request.centre_id)
        if not centre:
            raise NotFoundException(detail=f"Diagnostic centre with ID {request.centre_id} not found.")

        # Validate test
        test = db.get(DiagnosticTest, request.test_id)
        if not test:
            raise NotFoundException(detail=f"Diagnostic test with ID {request.test_id} not found.")

        # Verify centre offers this test and fetch snapshot price
        stmt = select(CentreTest).where(
            CentreTest.centre_id == request.centre_id,
            CentreTest.test_id == request.test_id,
        )
        centre_test = db.execute(stmt).scalar_one_or_none()
        if not centre_test:
            raise BadRequestException(
                detail=f"Diagnostic test '{test.name}' is not offered at centre '{centre.name}'."
            )

        # Create booking with snapshotted price
        booking = Booking(
            user_id=user_id,
            centre_id=request.centre_id,
            test_id=request.test_id,
            appointment_datetime=request.appointment_datetime,
            amount=centre_test.price,
            status=BookingStatus.PENDING,
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)

        logger.info(
            "Booking created successfully: ID=%d, User=%d, Centre=%d, Test=%d, Amount=%s",
            booking.id,
            user_id,
            booking.centre_id,
            booking.test_id,
            str(booking.amount),
        )
        return booking

    @staticmethod
    def list_user_bookings(db: Session, user_id: int) -> List[Booking]:
        """Retrieves all bookings owned by the authenticated user."""
        stmt = (
            select(Booking)
            .where(Booking.user_id == user_id)
            .order_by(Booking.created_at.desc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_booking_for_user(db: Session, booking_id: int, user_id: int) -> Booking:
        """
        Retrieves a single booking ensuring ownership.
        Returns 404 if not found, 403 if belonging to another user.
        """
        booking = db.get(Booking, booking_id)
        if not booking:
            raise NotFoundException(detail=f"Booking with ID {booking_id} not found.")

        if booking.user_id != user_id:
            raise ForbiddenException(detail="You do not have permission to view this booking.")

        return booking

    @staticmethod
    def cancel_booking(db: Session, booking_id: int, user_id: int) -> Booking:
        """
        Cancels a booking owned by the authenticated user.
        Validates state transitions (PENDING or CONFIRMED -> CANCELLED).
        """
        booking = BookingService.get_booking_for_user(db, booking_id, user_id)

        if booking.status == BookingStatus.CANCELLED:
            raise BadRequestException(detail="Booking is already cancelled.")

        if booking.status == BookingStatus.FAILED:
            raise BadRequestException(detail="Cannot cancel a booking that has already failed.")

        if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
            raise BadRequestException(
                detail=f"Cannot cancel booking with current status '{booking.status.value}'."
            )

        previous_status = booking.status.value
        booking.status = BookingStatus.CANCELLED
        db.commit()
        db.refresh(booking)

        logger.info(
            "Booking %d transitioned from %s to CANCELLED by User %d",
            booking.id,
            previous_status,
            user_id,
        )
        return booking
