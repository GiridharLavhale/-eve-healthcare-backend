"""Centre-test pricing and mapping schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.diagnostic_test import DiagnosticTestResponse


class CentreTestBase(BaseModel):
    price: Decimal = Field(..., gt=0, description="Test price in local currency, must be > 0", decimal_places=2)


class CentreTestCreate(CentreTestBase):
    test_id: int = Field(..., description="ID of the diagnostic test to offer")


class CentreTestResponse(BaseModel):
    id: int
    centre_id: int
    test_id: int
    price: Decimal
    created_at: datetime
    test: Optional[DiagnosticTestResponse] = None

    model_config = ConfigDict(from_attributes=True)
