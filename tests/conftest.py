"""Pytest fixtures and configuration for test execution."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import (
    User,
    DiagnosticCentre,
    DiagnosticTest,
    CentreTest,
    Booking,
    BookingStatus,
)

# In-memory SQLite for fast, isolated tests
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    expire_on_commit=False,
)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Creates a fresh database schema for each test function."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_data(db_session: Session) -> dict:
    """Pre-seeds standard diagnostic centres, tests, and pricing."""
    # Centre 1: Apollo
    c1 = DiagnosticCentre(name="Apollo Diagnostic Centre", location="Mumbai")
    # Centre 2: Metropolis
    c2 = DiagnosticCentre(name="Metropolis Healthcare", location="Bangalore")
    db_session.add_all([c1, c2])
    db_session.flush()

    # Tests
    t_cbc = DiagnosticTest(name="Complete Blood Count (CBC)", description="Measures blood cells")
    t_lipid = DiagnosticTest(name="Lipid Profile", description="Measures cholesterol")
    t_thyroid = DiagnosticTest(name="Thyroid Profile", description="Thyroid hormones")
    db_session.add_all([t_cbc, t_lipid, t_thyroid])
    db_session.flush()

    # Centre 1 pricing (CBC=500, Lipid=900)
    ct1 = CentreTest(centre_id=c1.id, test_id=t_cbc.id, price=Decimal("500.00"))
    ct2 = CentreTest(centre_id=c1.id, test_id=t_lipid.id, price=Decimal("900.00"))
    # Centre 2 pricing (CBC=420, Thyroid=700)
    ct3 = CentreTest(centre_id=c2.id, test_id=t_cbc.id, price=Decimal("420.00"))
    ct4 = CentreTest(centre_id=c2.id, test_id=t_thyroid.id, price=Decimal("700.00"))

    db_session.add_all([ct1, ct2, ct3, ct4])
    db_session.commit()

    return {
        "centre_1": c1,
        "centre_2": c2,
        "test_cbc": t_cbc,
        "test_lipid": t_lipid,
        "test_thyroid": t_thyroid,
    }


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Creates a standard test user."""
    user = User(
        email="john.doe@example.com",
        password_hash=hash_password("Password123!"),
        full_name="John Doe",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Generates valid JWT Authorization headers for test_user."""
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user(db_session: Session) -> User:
    """Creates a second distinct user for access control testing."""
    user = User(
        email="jane.smith@example.com",
        password_hash=hash_password("Password456!"),
        full_name="Jane Smith",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_auth_headers(second_user: User) -> dict:
    """Generates valid JWT Authorization headers for second_user."""
    token = create_access_token(subject=str(second_user.id))
    return {"Authorization": f"Bearer {token}"}
