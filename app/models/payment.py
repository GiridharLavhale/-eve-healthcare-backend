"""Payment database model and status enumeration."""

from decimal import Decimal
import enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.booking import Booking


class PaymentStatus(str, enum.Enum):
    """Lifecycle states for a payment transaction."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Payment(Base, TimestampMixin):
    """Payment transaction record."""
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_payment_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status_enum", native_enum=False, length=20),
        nullable=False,
        index=True,
    )

    # Relationships
    booking: Mapped["Booking"] = relationship(
        "Booking",
        back_populates="payments",
    )

    def __repr__(self) -> str:
        return f"<Payment id={self.id} booking_id={self.booking_id} status={self.status.value} amount={self.amount}>"
