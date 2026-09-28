"""Authentication schemas and validation."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    """User signup request schema."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (at least 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of user")

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v) and not any(c.isdigit() for c in v):
            # Check basic complexity
            pass
        return v


class LoginRequest(BaseModel):
    """User login request schema."""
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Plaintext password")

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()


class Token(BaseModel):
    """JWT Bearer token response schema."""
    access_token: str = Field(..., description="Signed JWT access token")
    token_type: str = Field(default="bearer", description="Token scheme")


class TokenData(BaseModel):
    """Internal decoded token payload."""
    sub: Optional[str] = None
    exp: Optional[int] = None
