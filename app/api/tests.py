"""Diagnostic test catalogue endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.diagnostic_test import (
    DiagnosticTestCreate,
    DiagnosticTestResponse,
)
from app.services.centre_service import CentreService

router = APIRouter(prefix="/tests", tags=["Diagnostic Tests"])


@router.get(
    "/",
    response_model=List[DiagnosticTestResponse],
    status_code=status.HTTP_200_OK,
    summary="List all diagnostic tests",
    description="Retrieves the global catalogue of all available diagnostic tests.",
)
def list_tests(db: Session = Depends(get_db)) -> List[DiagnosticTestResponse]:
    """Returns all diagnostic tests."""
    return CentreService.list_tests(db)


@router.post(
    "/",
    response_model=DiagnosticTestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a diagnostic test",
    description="Adds a new diagnostic test type to the global test catalogue.",
)
def create_test(
    request: DiagnosticTestCreate,
    db: Session = Depends(get_db),
) -> DiagnosticTestResponse:
    """Creates a new diagnostic test."""
    return CentreService.create_test(db=db, request=request)


@router.get(
    "/{test_id}",
    response_model=DiagnosticTestResponse,
    status_code=status.HTTP_200_OK,
    summary="Get diagnostic test by ID",
    description="Retrieves details of a specific diagnostic test from the catalogue.",
)
def get_test(
    test_id: int,
    db: Session = Depends(get_db),
) -> DiagnosticTestResponse:
    """Returns a specific diagnostic test."""
    return CentreService.get_test_by_id(db=db, test_id=test_id)
