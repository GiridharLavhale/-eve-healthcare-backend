"""Booking management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingCancelResponse,
)
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a diagnostic test booking",
    description="Creates a new diagnostic appointment for the authenticated user, capturing the centre test price at time of booking.",
)
def create_booking(
    request: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BookingResponse:
    """Creates a booking for the current authenticated user."""
    booking = BookingService.create_booking(
        db=db,
        user_id=current_user.id,
        request=request,
    )
    return booking


@router.get(
    "/",
    response_model=List[BookingResponse],
    status_code=status.HTTP_200_OK,
    summary="List current user bookings",
    description="Retrieves all appointment bookings created by the authenticated user.",
)
def list_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[BookingResponse]:
    """Returns bookings belonging strictly to the requesting user."""
    return BookingService.list_user_bookings(db=db, user_id=current_user.id)


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get booking details",
    description="Retrieves a specific booking by ID. Only the booking owner is authorized to view it.",
)
def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BookingResponse:
    """Returns booking details with ownership verification."""
    return BookingService.get_booking_for_user(
        db=db,
        booking_id=booking_id,
        user_id=current_user.id,
    )


@router.post(
    "/{booking_id}/cancel",
    response_model=BookingCancelResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel a booking",
    description="Allows the booking owner to cancel an active (PENDING or CONFIRMED) booking.",
)
def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BookingCancelResponse:
    """Cancels a booking owned by the authenticated user."""
    booking = BookingService.cancel_booking(
        db=db,
        booking_id=booking_id,
        user_id=current_user.id,
    )
    return BookingCancelResponse(
        id=booking.id,
        status=booking.status,
        message="Booking has been successfully cancelled.",
    )
