"""Booking database model and status enumeration."""

from datetime import datetime
from decimal import Decimal
import enum
from typing import List, TYPE_CHECKING
from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.diagnostic_centre import DiagnosticCentre
    from app.models.diagnostic_test import DiagnosticTest
    from app.models.payment import Payment


class BookingStatus(str, enum.Enum):
    """Lifecycle states for a diagnostic test booking."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Booking(Base, TimestampMixin):
    """Patient booking record for a diagnostic test at a centre."""
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    centre_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_centres.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    test_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_tests.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    appointment_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, name="booking_status_enum", native_enum=False, length=20),
        default=BookingStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="bookings",
        lazy="joined",
    )
    centre: Mapped["DiagnosticCentre"] = relationship(
        "DiagnosticCentre",
        back_populates="bookings",
        lazy="joined",
    )
    test: Mapped["DiagnosticTest"] = relationship(
        "DiagnosticTest",
        back_populates="bookings",
        lazy="joined",
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="booking",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Booking id={self.id} user_id={self.user_id} centre_id={self.centre_id} status={self.status.value}>"
