from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from typing import Any, Dict, List
from .logging import get_logger

logger = get_logger(__name__)


class ZibException(Exception):
    '''Base exception for Zib application'''
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ValidationException(ZibException):
    '''Exception for validation errors'''
    pass


class DatabaseException(ZibException):
    '''Exception for database-related errors'''
    pass


class FeedException(ZibException):
    '''Exception for feed-related errors'''
    pass


class CategoryException(ZibException):
    '''Exception for category-related errors'''
    pass


class FilterException(ZibException):
    '''Exception for filter-related errors'''
    pass


def format_validation_errors(validation_error: ValidationError) -> List[Dict[str, Any]]:
    '''Format Pydantic validation errors for API response'''
    errors = []
    
    for error in validation_error.errors():
        field_path = '.'.join(str(loc) for loc in error['loc'])
        errors.append({
            'field': field_path,
            'message': error['msg'],
            'type': error['type'],
            'input': error.get('input')
        })
    
    return errors


async def validation_exception_handler(request: Request, exc: ValidationError):
    '''Handle Pydantic validation exceptions'''
    logger.warning(f'Validation error on {request.url.path}: {exc}')
    
    errors = format_validation_errors(exc)
    
    return JSONResponse(
        status_code=422,
        content={
            'error': 'Validation Error',
            'message': 'The provided data is invalid',
            'details': {
                'errors': errors,
                'error_count': len(errors)
            }
        }
    )


async def zib_exception_handler(request: Request, exc: ZibException):
    '''Handle custom Zib exceptions'''
    logger.error(f'Zib exception on {request.url.path}: {exc.message}')
    
    # Determine status code based on exception type
    status_code = 500
    if isinstance(exc, ValidationException):
        status_code = 400
    elif isinstance(exc, (FeedException, CategoryException, FilterException)):
        status_code = 404  # Assuming resource not found
    elif isinstance(exc, DatabaseException):
        status_code = 500
    
    return JSONResponse(
        status_code=status_code,
        content={
            'error': exc.__class__.__name__,
            'message': exc.message,
            'details': exc.details
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    '''Handle FastAPI HTTP exceptions'''
    logger.warning(f'HTTP exception on {request.url.path}: {exc.detail}')
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': 'HTTP Error',
            'message': exc.detail,
            'details': {'status_code': exc.status_code}
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    '''Handle unexpected exceptions'''
    logger.error(f'Unexpected error on {request.url.path}: {exc}', exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'details': {'type': exc.__class__.__name__}
        }
    )