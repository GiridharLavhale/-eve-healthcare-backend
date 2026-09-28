"""Diagnostic test schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DiagnosticTestBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the diagnostic test")
    description: Optional[str] = Field(None, description="Detailed test description")


class DiagnosticTestCreate(DiagnosticTestBase):
    pass


class DiagnosticTestResponse(DiagnosticTestBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
