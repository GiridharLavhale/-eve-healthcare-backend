"""Diagnostic centre endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.diagnostic_centre import (
    DiagnosticCentreCreate,
    DiagnosticCentreResponse,
    DiagnosticCentreDetailResponse,
)
from app.schemas.centre_test import CentreTestCreate, CentreTestResponse
from app.services.centre_service import CentreService

router = APIRouter(prefix="/centres", tags=["Diagnostic Centres"])


@router.get(
    "/",
    response_model=List[DiagnosticCentreDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="List all diagnostic centres",
    description="Retrieves a list of all registered diagnostic centres with their available tests and prices.",
)
def list_centres(db: Session = Depends(get_db)) -> List[DiagnosticCentreDetailResponse]:
    """Returns all diagnostic centres with their test offerings."""
    return CentreService.list_centres(db)


@router.post(
    "/",
    response_model=DiagnosticCentreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create diagnostic centre",
    description="Registers a new diagnostic centre location.",
)
def create_centre(
    request: DiagnosticCentreCreate,
    db: Session = Depends(get_db),
) -> DiagnosticCentreResponse:
    """Creates a new diagnostic centre."""
    return CentreService.create_centre(db=db, request=request)


@router.get(
    "/{centre_id}",
    response_model=DiagnosticCentreDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get diagnostic centre by ID",
    description="Retrieves details of a specific diagnostic centre including offered tests.",
)
def get_centre(
    centre_id: int,
    db: Session = Depends(get_db),
) -> DiagnosticCentreDetailResponse:
    """Returns a specific diagnostic centre."""
    return CentreService.get_centre_by_id(db=db, centre_id=centre_id)


@router.get(
    "/{centre_id}/tests",
    response_model=List[CentreTestResponse],
    status_code=status.HTTP_200_OK,
    summary="Get tests offered by a centre",
    description="Lists all diagnostic tests and their specific prices offered by the specified centre.",
)
def get_centre_tests(
    centre_id: int,
    db: Session = Depends(get_db),
) -> List[CentreTestResponse]:
    """Returns test pricing for the specified centre."""
    return CentreService.get_centre_tests(db=db, centre_id=centre_id)


@router.post(
    "/{centre_id}/tests",
    response_model=CentreTestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Associate a test with a centre",
    description="Maps a diagnostic test to a centre with a specific price (or updates the price).",
)
def add_test_to_centre(
    centre_id: int,
    request: CentreTestCreate,
    db: Session = Depends(get_db),
) -> CentreTestResponse:
    """Links a test to a centre with pricing."""
    return CentreService.add_test_to_centre(db=db, centre_id=centre_id, request=request)
