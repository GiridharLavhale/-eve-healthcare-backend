"""Authentication and authorization endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import SignupRequest, LoginRequest, Token
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Registers a new patient/user with a validated email, secure password, and full name.",
)
def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Creates a new user record with securely hashed credentials."""
    user = AuthService.signup_user(db=db, request=request)
    return user


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates user credentials and issues a signed JWT Bearer access token.",
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> Token:
    """Authenticates email/password and generates an access token."""
    token = AuthService.authenticate_user(db=db, request=request)
    return token
