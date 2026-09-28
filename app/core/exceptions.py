"""Custom application exceptions and error handling utilities."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application HTTP exception."""

    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "A business error occurred.",
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundException(AppException):
    """Resource not found (HTTP 404)."""

    def __init__(self, detail: str = "Resource not found."):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BadRequestException(AppException):
    """Bad request or business validation failure (HTTP 400)."""

    def __init__(self, detail: str = "Invalid request payload or parameters."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ConflictException(AppException):
    """Resource conflict (e.g. unique constraint violation, duplicate resource) (HTTP 409)."""

    def __init__(self, detail: str = "Resource conflict detected."):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnauthorizedException(AppException):
    """Authentication required or failed (HTTP 401)."""

    def __init__(self, detail: str = "Authentication credentials are invalid or missing."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(AppException):
    """Access forbidden for the authenticated entity (HTTP 403)."""

    def __init__(self, detail: str = "You do not have permission to perform this action."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class UnprocessableEntityException(AppException):
    """Unprocessable entity (HTTP 422)."""

    def __init__(self, detail: str = "Unable to process request entity."):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)
