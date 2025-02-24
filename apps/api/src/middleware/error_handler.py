from typing import Any, Awaitable, Callable, Dict, Optional, Union

from fastapi import Request, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.exc import SQLAlchemyError

from ..utils.logger import logger


class ExperimentationError(Exception):
    """Base error for experimentation platform"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ExperimentationError):
    """Validation error"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details)


class ResourceNotFoundError(ExperimentationError):
    """Resource not found error"""

    def __init__(self, resource: str, resource_id: Union[str, int]):
        super().__init__(
            message=f"{resource} with id {resource_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "id": resource_id},
        )


async def error_handler(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Global error handling middleware"""
    try:
        return await call_next(request)

    except ExperimentationError as e:
        logger.error(
            f"Application error: {e.message}",
            extra={"status_code": e.status_code, "details": e.details, "path": request.url.path},
        )
        origin = request.headers.get("origin", "http://localhost:3000")
        return JSONResponse(
            status_code=e.status_code,
            content={"error": e.message, "details": e.details},
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            },
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}", extra={"path": request.url.path}, exc_info=True)
        origin = request.headers.get("origin", "http://localhost:3000")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Database error occurred", "details": {"message": str(e)}},
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            },
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={"path": request.url.path}, exc_info=True)
        origin = request.headers.get("origin", "http://localhost:3000")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "An unexpected error occurred", "details": {"message": str(e)}},
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            },
        )
