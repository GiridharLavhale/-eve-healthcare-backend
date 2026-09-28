"""Database seeder with realistic diagnostic centres, tests, and pricing data."""

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import Base, SessionLocal, engine
from app.core.logging import logger
from app.core.security import hash_password
from app.models import (
    DiagnosticCentre,
    DiagnosticTest,
    CentreTest,
    User,
)


def seed_database(db: Session | None = None) -> None:
    """Seeds the database with sample centres, tests, mappings, and a demo user."""
    should_close = False
    if db is None:
        # Ensure tables exist
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        should_close = True

    try:
        # 1. Seed Demo User
        stmt = select(User).where(User.email == "patient@example.com")
        existing_user = db.execute(stmt).scalar_one_or_none()
        if not existing_user:
            demo_user = User(
                email="patient@example.com",
                password_hash=hash_password("DemoPassword123!"),
                full_name="Sarah Connor",
            )
            db.add(demo_user)
            db.flush()
            logger.info("Created demo user: patient@example.com / DemoPassword123!")

        # 2. Seed Diagnostic Centres
        centres_data = [
            {"name": "Apollo Diagnostic Centre", "location": "Andheri West, Mumbai"},
            {"name": "Metropolis Healthcare", "location": "Koramangala, Bangalore"},
            {"name": "Suburban Diagnostics", "location": "Connaught Place, New Delhi"},
            {"name": "SRL Diagnostics", "location": "Banjara Hills, Hyderabad"},
        ]

        centre_entities = {}
        for c in centres_data:
            stmt = select(DiagnosticCentre).where(DiagnosticCentre.name == c["name"])
            centre = db.execute(stmt).scalar_one_or_none()
            if not centre:
                centre = DiagnosticCentre(name=c["name"], location=c["location"])
                db.add(centre)
                db.flush()
                logger.info("Created Diagnostic Centre: %s", centre.name)
            centre_entities[c["name"]] = centre

        # 3. Seed Diagnostic Tests
        tests_data = [
            {
                "name": "Complete Blood Count (CBC)",
                "description": "Measures red blood cells, white blood cells, and platelets to detect anemia, infection, and leukemia.",
            },
            {
                "name": "Lipid Profile",
                "description": "Measures total cholesterol, HDL, LDL, and triglycerides to evaluate cardiovascular health.",
            },
            {
                "name": "Thyroid Profile (T3, T4, TSH)",
                "description": "Evaluates thyroid gland performance and metabolic hormone balance.",
            },
            {
                "name": "Vitamin D (25-OH)",
                "description": "Assesses vitamin D sufficiency for bone health, calcium absorption, and immunity.",
            },
            {
                "name": "HbA1c (Glycated Hemoglobin)",
                "description": "Evaluates average blood sugar control over the past 90 days for diabetes monitoring.",
            },
            {
                "name": "Liver Function Test (LFT)",
                "description": "Assesses liver enzymes, bilirubin, and albumin to identify hepatic disorders.",
            },
        ]

        test_entities = {}
        for t in tests_data:
            stmt = select(DiagnosticTest).where(DiagnosticTest.name == t["name"])
            test = db.execute(stmt).scalar_one_or_none()
            if not test:
                test = DiagnosticTest(name=t["name"], description=t["description"])
                db.add(test)
                db.flush()
                logger.info("Created Diagnostic Test: %s", test.name)
            test_entities[t["name"]] = test

        # 4. Seed Centre-Test Mappings with specific pricing
        pricing_matrix = [
            # Apollo Diagnostic Centre
            ("Apollo Diagnostic Centre", "Complete Blood Count (CBC)", Decimal("450.00")),
            ("Apollo Diagnostic Centre", "Lipid Profile", Decimal("850.00")),
            ("Apollo Diagnostic Centre", "Thyroid Profile (T3, T4, TSH)", Decimal("700.00")),
            ("Apollo Diagnostic Centre", "Vitamin D (25-OH)", Decimal("1200.00")),
            ("Apollo Diagnostic Centre", "HbA1c (Glycated Hemoglobin)", Decimal("600.00")),
            ("Apollo Diagnostic Centre", "Liver Function Test (LFT)", Decimal("900.00")),

            # Metropolis Healthcare
            ("Metropolis Healthcare", "Complete Blood Count (CBC)", Decimal("400.00")),
            ("Metropolis Healthcare", "Lipid Profile", Decimal("800.00")),
            ("Metropolis Healthcare", "Thyroid Profile (T3, T4, TSH)", Decimal("650.00")),
            ("Metropolis Healthcare", "Vitamin D (25-OH)", Decimal("1100.00")),
            ("Metropolis Healthcare", "HbA1c (Glycated Hemoglobin)", Decimal("550.00")),

            # Suburban Diagnostics
            ("Suburban Diagnostics", "Complete Blood Count (CBC)", Decimal("500.00")),
            ("Suburban Diagnostics", "Lipid Profile", Decimal("900.00")),
            ("Suburban Diagnostics", "Thyroid Profile (T3, T4, TSH)", Decimal("750.00")),
            ("Suburban Diagnostics", "Liver Function Test (LFT)", Decimal("950.00")),

            # SRL Diagnostics
            ("SRL Diagnostics", "Complete Blood Count (CBC)", Decimal("420.00")),
            ("SRL Diagnostics", "Vitamin D (25-OH)", Decimal("1150.00")),
            ("SRL Diagnostics", "HbA1c (Glycated Hemoglobin)", Decimal("580.00")),
        ]

        for centre_name, test_name, price in pricing_matrix:
            centre = centre_entities.get(centre_name)
            test = test_entities.get(test_name)
            if centre and test:
                stmt = select(CentreTest).where(
                    CentreTest.centre_id == centre.id,
                    CentreTest.test_id == test.id,
                )
                mapping = db.execute(stmt).scalar_one_or_none()
                if not mapping:
                    mapping = CentreTest(
                        centre_id=centre.id,
                        test_id=test.id,
                        price=price,
                    )
                    db.add(mapping)

        db.commit()
        logger.info("Database successfully seeded with realistic sample data.")

    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed database: %s", str(exc))
        raise
    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    seed_database()
