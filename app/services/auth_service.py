"""Authentication and user management business logic."""

from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.exceptions import ConflictException, NotFoundException, UnauthorizedException
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest, Token


class AuthService:
    """Service handling user registration, authentication, and token generation."""

    @staticmethod
    def signup_user(db: Session, request: SignupRequest) -> User:
        """Registers a new user after validating uniqueness and hashing the password."""
        email_normalized = request.email.strip().lower()

        # Check for existing user
        stmt = select(User).where(User.email == email_normalized)
        existing_user = db.execute(stmt).scalar_one_or_none()
        if existing_user:
            raise ConflictException(detail="A user with this email address already exists.")

        # Create user entity
        user = User(
            email=email_normalized,
            password_hash=hash_password(request.password),
            full_name=request.full_name.strip(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, request: LoginRequest) -> Token:
        """Authenticates user credentials and returns a signed JWT access token."""
        email_normalized = request.email.strip().lower()

        stmt = select(User).where(User.email == email_normalized)
        user = db.execute(stmt).scalar_one_or_none()

        if not user or not verify_password(request.password, user.password_hash):
            raise UnauthorizedException(detail="Invalid email or password.")

        access_token = create_access_token(subject=str(user.id))
        return Token(access_token=access_token, token_type="bearer")

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Fetches a user by their primary key ID."""
        user = db.get(User, user_id)
        if not user:
            raise NotFoundException(detail="User not found.")
        return user
