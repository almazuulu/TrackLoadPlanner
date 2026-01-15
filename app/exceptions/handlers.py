from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.
    """
    errors = []
    for error in exc.errors():
        error_detail = {
            "loc": list(error.get("loc", [])),
            "msg": error.get("msg", "Validation error"),
            "type": error.get("type", "value_error")
        }
        errors.append(error_detail)
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions.
    
    Catches any unhandled exception and returns a generic 500 error.
    In production, this should log the error for debugging.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error"
        }
    )
