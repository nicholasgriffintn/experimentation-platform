from typing import Any, Dict, Union

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from ..utils.logger import logger


class ExperimentationError(Exception):
    """Base error for experimentation platform"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Dict[str, Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ExperimentationError):
    """Validation error"""

    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details)


class ResourceNotFoundError(ExperimentationError):
    """Resource not found error"""

    def __init__(self, resource: str, resource_id: Union[str, int]):
        super().__init__(
            message=f"{resource} with id {resource_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "id": resource_id},
        )


async def error_handler(request: Request, call_next):
    """Global error handling middleware"""
    try:
        return await call_next(request)

    except ExperimentationError as e:
        logger.error(
            f"Application error: {e.message}",
            extra={"status_code": e.status_code, "details": e.details, "path": request.url.path},
        )
        return JSONResponse(
            status_code=e.status_code, content={"error": e.message, "details": e.details}
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}", extra={"path": request.url.path}, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Database error occurred", "details": {"message": str(e)}},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={"path": request.url.path}, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "An unexpected error occurred", "details": {"message": str(e)}},
        )
