"""Diagnostic centre database model."""

from typing import List, TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.centre_test import CentreTest
    from app.models.booking import Booking


class DiagnosticCentre(Base, TimestampMixin):
    """Diagnostic centre entity."""
    __tablename__ = "diagnostic_centres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    centre_tests: Mapped[List["CentreTest"]] = relationship(
        "CentreTest",
        back_populates="centre",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking",
        back_populates="centre",
    )

    def __repr__(self) -> str:
        return f"<DiagnosticCentre id={self.id} name='{self.name}'>"
