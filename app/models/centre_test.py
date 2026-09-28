"""Diagnostic centre and test mapping database model with custom pricing."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.diagnostic_centre import DiagnosticCentre
    from app.models.diagnostic_test import DiagnosticTest


class CentreTest(Base):
    """Represents a diagnostic test offered by a specific centre with a specific price."""
    __tablename__ = "centre_tests"
    __table_args__ = (
        UniqueConstraint("centre_id", "test_id", name="uq_centre_test"),
        CheckConstraint("price > 0", name="chk_centre_test_price_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    centre_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_centres.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    centre: Mapped["DiagnosticCentre"] = relationship(
        "DiagnosticCentre",
        back_populates="centre_tests",
        lazy="joined",
    )
    test: Mapped["DiagnosticTest"] = relationship(
        "DiagnosticTest",
        back_populates="centre_tests",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<CentreTest id={self.id} centre_id={self.centre_id} test_id={self.test_id} price={self.price}>"
