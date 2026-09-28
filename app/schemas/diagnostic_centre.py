"""Diagnostic centre schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.centre_test import CentreTestResponse


class DiagnosticCentreBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Centre name")
    location: str = Field(..., min_length=1, max_length=255, description="Centre location / address")


class DiagnosticCentreCreate(DiagnosticCentreBase):
    pass


class DiagnosticCentreResponse(DiagnosticCentreBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiagnosticCentreDetailResponse(DiagnosticCentreResponse):
    centre_tests: List[CentreTestResponse] = Field(
        default_factory=list,
        description="List of tests offered at this centre with their respective prices",
    )

    model_config = ConfigDict(from_attributes=True)
