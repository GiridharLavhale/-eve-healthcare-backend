"""Diagnostic test database model."""

from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.centre_test import CentreTest
    from app.models.booking import Booking


class DiagnosticTest(Base, TimestampMixin):
    """Diagnostic test entity (e.g. CBC, Lipid Profile)."""
    __tablename__ = "diagnostic_tests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    centre_tests: Mapped[List["CentreTest"]] = relationship(
        "CentreTest",
        back_populates="test",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking",
        back_populates="test",
    )

    def __repr__(self) -> str:
        return f"<DiagnosticTest id={self.id} name='{self.name}'>"
