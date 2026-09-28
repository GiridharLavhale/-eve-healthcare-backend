"""Diagnostic centre and test management business logic."""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.exceptions import ConflictException, NotFoundException
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.diagnostic_test import DiagnosticTest
from app.models.centre_test import CentreTest
from app.schemas.diagnostic_centre import DiagnosticCentreCreate
from app.schemas.diagnostic_test import DiagnosticTestCreate
from app.schemas.centre_test import CentreTestCreate


class CentreService:
    """Service handling diagnostic centres, diagnostic tests, and pricing associations."""

    @staticmethod
    def list_centres(db: Session) -> List[DiagnosticCentre]:
        """Retrieves all diagnostic centres."""
        stmt = select(DiagnosticCentre).order_by(DiagnosticCentre.id.asc())
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_centre_by_id(db: Session, centre_id: int) -> DiagnosticCentre:
        """Retrieves a diagnostic centre by ID or raises 404."""
        centre = db.get(DiagnosticCentre, centre_id)
        if not centre:
            raise NotFoundException(detail=f"Diagnostic centre with ID {centre_id} not found.")
        return centre

    @staticmethod
    def create_centre(db: Session, request: DiagnosticCentreCreate) -> DiagnosticCentre:
        """Creates a new diagnostic centre."""
        centre = DiagnosticCentre(
            name=request.name.strip(),
            location=request.location.strip(),
        )
        db.add(centre)
        db.commit()
        db.refresh(centre)
        return centre

    @staticmethod
    def list_tests(db: Session) -> List[DiagnosticTest]:
        """Retrieves all available diagnostic tests."""
        stmt = select(DiagnosticTest).order_by(DiagnosticTest.id.asc())
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_test_by_id(db: Session, test_id: int) -> DiagnosticTest:
        """Retrieves a diagnostic test by ID or raises 404."""
        test = db.get(DiagnosticTest, test_id)
        if not test:
            raise NotFoundException(detail=f"Diagnostic test with ID {test_id} not found.")
        return test

    @staticmethod
    def create_test(db: Session, request: DiagnosticTestCreate) -> DiagnosticTest:
        """Creates a new diagnostic test entity."""
        name_clean = request.name.strip()
        stmt = select(DiagnosticTest).where(DiagnosticTest.name == name_clean)
        existing = db.execute(stmt).scalar_one_or_none()
        if existing:
            raise ConflictException(detail=f"Diagnostic test '{name_clean}' already exists.")

        test = DiagnosticTest(
            name=name_clean,
            description=request.description.strip() if request.description else None,
        )
        db.add(test)
        db.commit()
        db.refresh(test)
        return test

    @staticmethod
    def get_centre_tests(db: Session, centre_id: int) -> List[CentreTest]:
        """Retrieves all tests offered at a specific centre along with their prices."""
        # Ensure centre exists first
        CentreService.get_centre_by_id(db, centre_id)

        stmt = (
            select(CentreTest)
            .where(CentreTest.centre_id == centre_id)
            .order_by(CentreTest.id.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def add_test_to_centre(db: Session, centre_id: int, request: CentreTestCreate) -> CentreTest:
        """Links a diagnostic test to a centre with a specified price."""
        centre = CentreService.get_centre_by_id(db, centre_id)
        test = CentreService.get_test_by_id(db, request.test_id)

        stmt = select(CentreTest).where(
            CentreTest.centre_id == centre.id,
            CentreTest.test_id == test.id,
        )
        existing = db.execute(stmt).scalar_one_or_none()
        if existing:
            # Update price if already mapped
            existing.price = request.price
            db.commit()
            db.refresh(existing)
            return existing

        centre_test = CentreTest(
            centre_id=centre.id,
            test_id=test.id,
            price=request.price,
        )
        db.add(centre_test)
        db.commit()
        db.refresh(centre_test)
        return centre_test
