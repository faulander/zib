from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ErrorResponse(BaseModel):
    '''Standard error response schema'''
    error: str = Field(..., description='Error type or category')
    message: str = Field(..., description='Human-readable error message')
    details: Optional[Dict[str, Any]] = Field(None, description='Additional error details')


class SuccessResponse(BaseModel):
    '''Standard success response schema'''
    message: str = Field(..., description='Success message')
    data: Optional[Dict[str, Any]] = Field(None, description='Response data')


class PaginatedResponse(BaseModel):
    '''Paginated response schema'''
    items: List[Dict[str, Any]] = Field(..., description='List of items for current page')
    total: int = Field(..., ge=0, description='Total number of items')
    page: int = Field(..., ge=1, description='Current page number')
    page_size: int = Field(..., ge=1, le=100, description='Number of items per page')
    pages: int = Field(..., ge=1, description='Total number of pages')


class BaseSchema(BaseModel):
    '''Base schema with common configuration'''
    
    class Config:
        from_attributes = True
        str_strip_whitespace = True
        validate_assignment = True